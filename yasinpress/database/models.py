"""Persistence models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


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
