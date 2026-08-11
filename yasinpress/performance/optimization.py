"""Optimization helpers."""

from functools import lru_cache


@lru_cache(maxsize=1024)
def normalized_key(value: str) -> str:
    """Normalize and cache keys used in hot paths."""
    return value.strip().lower()
