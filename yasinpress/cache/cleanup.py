"""Cache cleanup."""
from time import time
from .storage import CacheStorage


def cleanup_expired(storage: CacheStorage) -> int:
    """Remove expired cache entries and return count."""
    expired = [key for key, entry in storage.entries.items() if entry.expires_at <= time()]
    for key in expired: del storage.entries[key]
    return len(expired)
