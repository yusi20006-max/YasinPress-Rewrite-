from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class WatchdogStatus:
    last_tick_at: datetime | None
    consecutive_failures: int
    healthy: bool
    last_error: str | None


class Watchdog:
    """Small runtime supervisor that turns worker failures into observable state."""

    def __init__(self, stale_after: timedelta = timedelta(minutes=2)) -> None:
        self.stale_after = stale_after
        self.last_tick_at: datetime | None = None
        self.consecutive_failures = 0
        self.last_error: str | None = None

    def record_success(self, now: datetime | None = None) -> None:
        self.last_tick_at = now or datetime.now(UTC)
        self.consecutive_failures = 0
        self.last_error = None

    def record_failure(self, error: Exception | str, now: datetime | None = None) -> None:
        self.last_tick_at = now or datetime.now(UTC)
        self.consecutive_failures += 1
        self.last_error = str(error)

    def status(self, now: datetime | None = None) -> WatchdogStatus:
        current = now or datetime.now(UTC)
        healthy = self.last_tick_at is not None and current - self.last_tick_at <= self.stale_after and self.consecutive_failures == 0
        return WatchdogStatus(self.last_tick_at, self.consecutive_failures, healthy, self.last_error)
