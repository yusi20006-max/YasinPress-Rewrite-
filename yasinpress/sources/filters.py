"""Source filtering utilities."""
from .feed import FeedItem

class KeywordFilter:
    """Filter feed items by required and blocked keywords."""
    def __init__(self, required: set[str] | None = None, blocked: set[str] | None = None) -> None:
        self.required = {word.lower() for word in (required or set())}
        self.blocked = {word.lower() for word in (blocked or set())}

    def allow(self, item: FeedItem) -> bool:
        """Return whether an item passes the filter."""
        text = f"{item.title} {item.content}".lower()
        return (not self.required or any(word in text for word in self.required)) and not any(word in text for word in self.blocked)
