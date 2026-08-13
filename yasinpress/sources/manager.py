"""Source registry and health manager."""

import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from yasinpress.sources.feed import FeedItem, parse_rss


@dataclass
class Source:
    """RSS source definition with health tracking."""

    name: str
    url: str
    enabled: bool = True
    status: str = "healthy"  # healthy, degraded, failed
    last_success: datetime | None = None
    last_failure: datetime | None = None
    response_time: float | None = None
    consecutive_failures: int = 0
    success_count: int = 0
    failure_count: int = 0
    stale_count: int = 0


class SourceManager:
    """Manage configured sources."""

    def __init__(self, sources: list[Source] | None = None) -> None:
        self._sources = sources or []

    def add(self, source: Source) -> None:
        """Register a source."""
        self._sources.append(source)

    def enabled(self) -> list[Source]:
        """Return enabled sources."""
        return [source for source in self._sources if source.enabled]

    def get(self, name: str) -> Source | None:
        """Get source by name."""
        for s in self._sources:
            if s.name == name:
                return s
        return None


def ingest_source(
    source: Source,
    fetch_engine,
    stale_threshold_hours: float = 24.0,
) -> list[FeedItem]:
    """Fetch and parse feed items for a single source, updating health metrics."""
    if not source.enabled:
        return []

    start_time = time.perf_counter()
    try:
        if hasattr(fetch_engine, "fetch"):
            payload = fetch_engine.fetch(source.url)
        elif callable(fetch_engine):
            payload = fetch_engine(source.url)
        else:
            raise ValueError("Invalid fetch engine provided")

        elapsed = time.perf_counter() - start_time
        source.response_time = elapsed
        source.last_success = datetime.now(UTC)
        source.success_count += 1
        source.consecutive_failures = 0

        items = parse_rss(payload)

        if items:
            now = datetime.now(UTC)
            stale_threshold = timedelta(hours=stale_threshold_hours)
            valid_dates = []
            for item in items:
                pub = item.published_at
                if pub is None:
                    continue
                if pub.tzinfo is None:
                    pub = pub.replace(tzinfo=UTC)
                else:
                    pub = pub.astimezone(UTC)
                # The parser uses Unix epoch for missing/invalid publication
                # dates. Such items must not make an otherwise healthy source
                # look stale; freshness filtering is handled by the pipeline.
                if pub == datetime.fromtimestamp(0, tz=UTC):
                    continue
                valid_dates.append(pub)

            if valid_dates and all(now - pub > stale_threshold for pub in valid_dates):
                source.stale_count += 1
                source.status = "degraded"
            else:
                source.stale_count = 0
                source.status = "healthy"
                source.enabled = True
        else:
            source.status = "degraded"
            source.stale_count += 1

        return [
            FeedItem(
                title=item.title,
                url=item.url,
                content=item.content,
                published_at=item.published_at,
                source=source.name,
                media_url=item.media_url,
                media_type=item.media_type,
            )
            for item in items
        ]

    except Exception:
        elapsed = time.perf_counter() - start_time
        source.response_time = elapsed
        source.last_failure = datetime.now(UTC)
        source.failure_count += 1
        source.consecutive_failures += 1

        if source.consecutive_failures >= 3:
            source.status = "failed"
            source.enabled = False
        else:
            source.status = "degraded"

        return []
