"""In-memory cache storage."""

from dataclasses import dataclass
from time import time


@dataclass(frozen=True)
class CacheEntry:
    """A cached value with expiration."""

    value: str
    expires_at: float


class CacheStorage:
    """Dictionary-backed cache storage."""

    def __init__(self) -> None:
        self.entries: dict[str, CacheEntry] = {}

    def set(self, key: str, value: str, ttl: float) -> None:
        """Store a value."""
        self.entries[key] = CacheEntry(value, time() + ttl)

    def get(self, key: str) -> str | None:
        """Return unexpired value."""
        entry = self.entries.get(key)
        return entry.value if entry and entry.expires_at > time() else None
