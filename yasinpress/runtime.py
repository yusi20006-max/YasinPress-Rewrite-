from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from threading import Event


class Runtime:
    """Small lifecycle controller for long-running YasinPress workers."""

    def __init__(self, tick: Callable[[], None], interval_seconds: float = 1.0) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self.tick = tick
        self.interval_seconds = interval_seconds
        self._stop = Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        while not self._stop.is_set():
            self.tick()
            self._stop.wait(self.interval_seconds)

    def close(self) -> None:
        self.stop()
        with suppress(Exception):
            self.tick = lambda: None
