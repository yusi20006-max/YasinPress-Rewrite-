"""Persistence models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

#: Priority tiers, highest first. Used to order fair batch selection.
PRIORITY_LEVELS: tuple[str, ...] = ("breaking", "urgent", "important", "normal")


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
    priority: str = "normal"
    is_ai_rewritten: bool = False

    def __post_init__(self) -> None:
        if self.priority not in PRIORITY_LEVELS:
            object.__setattr__(self, "priority", "normal")
