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
