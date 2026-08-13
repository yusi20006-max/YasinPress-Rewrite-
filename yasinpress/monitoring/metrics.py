"""Metrics registry."""

from collections import Counter
from typing import Any

from yasinpress.monitoring.snapshot import RuntimeSnapshot


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


def dashboard_metrics(snapshot: RuntimeSnapshot) -> dict[str, Any]:
    """Convert RuntimeSnapshot to JSON-safe dashboard metrics dictionary."""
    return {
        "captured_at": snapshot.captured_at.isoformat(),
        "queue": {
            "pending": snapshot.queue_pending,
            "processing": snapshot.queue_processing,
            "retrying": snapshot.queue_retrying,
            "failed": snapshot.queue_failed,
            "dead_letter": snapshot.queue_dead_letter,
        },
        "published_last_hour": snapshot.published_last_hour,
        "source_health": snapshot.source_health,
    }
