from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta

from yasinpress.scheduler import Scheduler
from yasinpress.watchdog import Watchdog


class RuntimeScheduler:
    """Production runtime composition: Scheduler + watchdog + business tick."""

    def __init__(
        self,
        tick: Callable[[], object | None],
        *,
        interval: timedelta = timedelta(seconds=60),
        watchdog: Watchdog | None = None,
    ) -> None:
        self.scheduler = Scheduler(tick, interval=interval, watchdog=watchdog)

    @property
    def watchdog(self) -> Watchdog:
        return self.scheduler.watchdog

    def start(self, *, max_ticks: int | None = None) -> int:
        return self.scheduler.run(max_ticks=max_ticks)

    def tick_once(self) -> object | None:
        return self.scheduler.run_once()

    def stop(self) -> None:
        self.scheduler.stop()
