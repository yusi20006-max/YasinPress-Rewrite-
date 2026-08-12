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
    published_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    category: str | None = None
    ai_modified: bool = False
    event_id: str | None = None
    received_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    lifecycle_state: str = "fetched"
    ai_state: str = "none"
    ai_error: str | None = None
    source_metadata: dict[str, object] = field(default_factory=dict)

    @property
    def age(self) -> timedelta:
        """Return the age of the article relative to UTC now."""
        pub = self.published_at
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=UTC)
        else:
            pub = pub.astimezone(UTC)
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
