"""Metrics registry."""

from collections import Counter


class Metrics:
    """In-process counter metrics."""

    def __init__(self) -> None:
        self._counters: Counter[str] = Counter()

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter."""
        self._counters[name] += value

    def snapshot(self) -> dict[str, int]:
        """Return metric snapshot."""
        return dict(self._counters)
