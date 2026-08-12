from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from threading import Event

from yasinpress.watchdog import Watchdog


class Runtime:
    """Lifecycle controller for a long-running YasinPress worker.

    A failed tick is isolated from the process, while an optional recovery hook
    can repair durable state before the next tick. The runtime never performs
    business logic itself.
    """

    def __init__(
        self,
        tick: Callable[[], None],
        interval_seconds: float = 1.0,
        watchdog: Watchdog | None = None,
        recover: Callable[[], None] | None = None,
        max_consecutive_failures: int = 3,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        if max_consecutive_failures <= 0:
            raise ValueError("max_consecutive_failures must be positive")
        self.tick = tick
        self.interval_seconds = interval_seconds
        self.watchdog = watchdog or Watchdog()
        self.recover = recover
        self.max_consecutive_failures = max_consecutive_failures
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
                if self.watchdog.consecutive_failures >= self.max_consecutive_failures and self.recover:
                    try:
                        self.recover()
                    except Exception as recovery_error:
                        self.watchdog.record_failure(recovery_error)
                    else:
                        self.watchdog.record_success()
            else:
                self.watchdog.record_success()
            self._stop.wait(self.interval_seconds)

    def close(self) -> None:
        self.stop()
        with suppress(Exception):
            self.tick = lambda: None
