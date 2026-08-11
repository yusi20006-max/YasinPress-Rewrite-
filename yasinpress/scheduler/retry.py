"""Retry policy."""

from collections.abc import Callable
import time


class RetryPolicy:
    """Simple exponential retry policy."""

    def __init__(self, attempts: int = 3, delay: float = 0.1) -> None:
        self.attempts = attempts
        self.delay = delay

    def run(self, func: Callable[[], None]) -> None:
        """Run callable with retries."""
        last_error: Exception | None = None
        for attempt in range(self.attempts):
            try:
                func()
                return
            except Exception as exc:  # noqa: BLE001 - retry boundary must capture task failures
                last_error = exc
                time.sleep(self.delay * (2**attempt))
        if last_error:
            raise last_error
