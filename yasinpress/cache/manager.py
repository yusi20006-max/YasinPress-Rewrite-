"""Cache manager."""

from collections.abc import Callable

from .storage import CacheStorage


class CacheManager:
    """High-level cache API."""

    def __init__(self, storage: CacheStorage | None = None, default_ttl: float = 300) -> None:
        self.storage = storage or CacheStorage()
        self.default_ttl = default_ttl

    def remember(self, key: str, factory: Callable[[], object], ttl: float | None = None) -> str:
        """Return cached value or compute and store it."""
        cached = self.storage.get(key)
        if cached is not None:
            return cached
        value = str(factory())
        self.storage.set(key, value, ttl or self.default_ttl)
        return value
