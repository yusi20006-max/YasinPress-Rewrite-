"""Persistence models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class Article:
    """A normalized news article."""

    id: str
    title: str
    url: str
    content: str
    source: str
    published_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    category: str | None = None
    event_id: str | None = None
    received_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    lifecycle_state: str = "fetched"
    ai_state: str = "none"
    ai_error: str | None = None
    source_metadata: str | None = None

    @property
    def age(self) -> timedelta:
        """Calculate age from publication time relative to current UTC time."""
        now_utc = datetime.now(UTC)
        pub = self.published_at
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=UTC)
        return now_utc - pub
