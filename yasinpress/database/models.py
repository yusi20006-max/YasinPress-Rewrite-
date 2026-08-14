"""Persistence models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class Article:
    """A normalized news article and its processing provenance."""

    id: str
    title: str
    url: str
    content: str
    source: str
    published_at: datetime | None = None
    category: str | None = None
    ai_modified: bool = False
    event_id: str | None = None
    received_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    lifecycle_state: str = "fetched"
    ai_state: str = "none"
    ai_error: str | None = None
    source_metadata: dict[str, object] = field(default_factory=dict)
    updated_at: datetime | None = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    processed_at: datetime | None = None
    published_to_channel_at: datetime | None = None

    @property
    def news_timestamp(self) -> datetime | None:
        """Return the most specific valid timezone-aware timestamp representing the news time."""
        for dt_val in [self.updated_at, self.published_at]:
            if dt_val is not None and dt_val != datetime.fromtimestamp(0, tz=UTC):
                if dt_val.tzinfo is None:
                    return dt_val.replace(tzinfo=UTC)
                return dt_val.astimezone(UTC)
        return None

    @property
    def age(self) -> timedelta:
        """Return the age of the article relative to UTC now."""
        pub = self.news_timestamp
        if pub is None:
            return timedelta(days=999)
        return datetime.now(UTC) - pub


@dataclass
class PublicationJob:
    """A persistent news publication unit of work."""

    id: str  # f"{article_id}:{destination}"
    article_id: str
    destination: str
    status: str  # 'pending', 'processing', 'retrying', 'failed', 'dead_letter', 'succeeded'
    priority: int
    priority_level: str  # 'breaking', 'urgent', 'important', 'normal'
    source: str
    attempts: int = 0
    max_attempts: int = 3
    last_error: str | None = None
    lease_expires_at: datetime | None = None
    next_attempt_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
