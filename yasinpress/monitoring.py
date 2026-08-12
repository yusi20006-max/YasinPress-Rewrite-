from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class RuntimeSnapshot:
    captured_at: datetime
    queue_pending: int
    queue_processing: int
    queue_retrying: int
    queue_failed: int
    queue_dead_letter: int
    published_last_hour: int
    source_health: dict[str, dict[str, object]]


def snapshot(queue) -> RuntimeSnapshot:
    """Build a reporting-safe snapshot from the persistent publication queue."""
    metrics = queue.metrics()
    health = queue.source_health() if hasattr(queue, "source_health") else {}
    return RuntimeSnapshot(
        captured_at=datetime.now(UTC),
        queue_pending=int(metrics.get("pending", 0)),
        queue_processing=int(metrics.get("processing", 0)),
        queue_retrying=int(metrics.get("retrying", 0)),
        queue_failed=int(metrics.get("failed", 0)),
        queue_dead_letter=int(metrics.get("dead_letter", 0)),
        published_last_hour=int(metrics.get("published_last_hour", 0)),
        source_health=health,
    )


def hourly_report(snapshot: RuntimeSnapshot) -> dict[str, object]:
    """Return the stable payload used by hourly reports and the future PWA API."""
    return {
        "timestamp": snapshot.captured_at.isoformat(),
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
