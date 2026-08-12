from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from threading import Event

from yasinpress.watchdog import Watchdog


class Runtime:
    """Small lifecycle controller for long-running YasinPress workers."""

    def __init__(
        self,
        tick: Callable[[], None],
        interval_seconds: float = 1.0,
        watchdog: Watchdog | None = None,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self.tick = tick
        self.interval_seconds = interval_seconds
        self.watchdog = watchdog or Watchdog()
        self._stop = Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        print("YasinPress is active", flush=True)
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception as exc:
                self.watchdog.record_failure(exc)
            else:
                self.watchdog.record_success()
            self._stop.wait(self.interval_seconds)

    def close(self) -> None:
        self.stop()
        with suppress(Exception):
            self.tick = lambda: None
