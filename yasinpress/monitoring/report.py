from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class OperationalReport:
    """Single source of truth for the hourly operational snapshot."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    received: int = 0
    accepted: int = 0
    rejected: int = 0
    expired: int = 0
    duplicates: int = 0
    queue_depth: int = 0
    published: int = 0
    failed: int = 0
    retrying: int = 0
    ai_processed: int = 0
    ai_modified: int = 0
    sources_total: int = 0
    sources_active: int = 0
    sources_inactive: int = 0
    sources_degraded: int = 0
    internet_ok: bool = False
    publisher_ok: bool = False
    scheduler_ok: bool = False
    watchdog_ok: bool = False
    uptime_seconds: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp.astimezone(UTC).isoformat(),
            "received": self.received,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "expired": self.expired,
            "duplicates": self.duplicates,
            "queue_depth": self.queue_depth,
            "published": self.published,
            "failed": self.failed,
            "retrying": self.retrying,
            "ai_processed": self.ai_processed,
            "ai_modified": self.ai_modified,
            "sources_total": self.sources_total,
            "sources_active": self.sources_active,
            "sources_inactive": self.sources_inactive,
            "sources_degraded": self.sources_degraded,
            "internet_ok": self.internet_ok,
            "publisher_ok": self.publisher_ok,
            "scheduler_ok": self.scheduler_ok,
            "watchdog_ok": self.watchdog_ok,
            "uptime_seconds": self.uptime_seconds,
        }

    def to_text(self) -> str:
        status = lambda value: "OK" if value else "DOWN"
        return "\n".join(
            [
                f"YasinPress hourly report — {self.timestamp.astimezone(UTC).isoformat()}",
                f"News: received={self.received} accepted={self.accepted} rejected={self.rejected} expired={self.expired} duplicates={self.duplicates}",
                f"Queue: depth={self.queue_depth} published={self.published} failed={self.failed} retrying={self.retrying}",
                f"AI: processed={self.ai_processed} modified={self.ai_modified}",
                f"Sources: total={self.sources_total} active={self.sources_active} inactive={self.sources_inactive} degraded={self.sources_degraded}",
                f"Health: internet={status(self.internet_ok)} publisher={status(self.publisher_ok)} scheduler={status(self.scheduler_ok)} watchdog={status(self.watchdog_ok)}",
                f"Uptime: {self.uptime_seconds:.0f}s",
            ]
        )
