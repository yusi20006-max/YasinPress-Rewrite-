from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from threading import Event, Lock

from yasinpress.watchdog import Watchdog


class Scheduler:
    """Deterministic single-flight scheduler for runtime callbacks.

    Business logic stays in callbacks; the scheduler owns cadence, overlap
    prevention, heartbeat recording, and graceful shutdown.
    """

    def __init__(
        self,
        tick: Callable[[], object | None],
        *,
        interval: timedelta = timedelta(seconds=60),
        watchdog: Watchdog | None = None,
    ) -> None:
        if interval <= timedelta(0):
            raise ValueError("interval must be positive")
        self.tick = tick
        self.interval = interval
        self.watchdog = watchdog or Watchdog(stale_after=max(interval * 3, timedelta(minutes=2)))
        self._stop = Event()
        self._running = Lock()
        self.last_result: object | None = None
        self.last_error: str | None = None
        self.ticks = 0

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    def stop(self) -> None:
        self._stop.set()

    def run(self, *, max_ticks: int | None = None) -> int:
        if max_ticks is not None and max_ticks < 0:
            raise ValueError("max_ticks must be non-negative")
        completed = 0
        while not self.stopped and (max_ticks is None or completed < max_ticks):
            self.run_once()
            completed += 1
            if self.stopped or (max_ticks is not None and completed >= max_ticks):
                break
            self._stop.wait(self.interval.total_seconds())
        return completed

    def run_once(self, now: datetime | None = None) -> object | None:
        if self.stopped:
            return None
        if not self._running.acquire(blocking=False):
            return None
        current = _utc(now)
        try:
            try:
                result = self.tick()
            except Exception as exc:  # scheduler boundary; worker failures stay isolated
                self.last_error = str(exc)
                self.watchdog.record_failure(exc, current)
                return None
            self.last_result = result
            self.last_error = None
            self.watchdog.record_success(current)
            self.ticks += 1
            return result
        finally:
            self._running.release()


def _utc(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    return current.replace(tzinfo=UTC) if current.tzinfo is None else current.astimezone(UTC)
