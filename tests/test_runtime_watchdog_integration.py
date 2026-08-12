from datetime import UTC

from yasinpress.runtime import Runtime
from yasinpress.watchdog import Watchdog


def test_runtime_records_success():
    watchdog = Watchdog()
    calls = []

    def tick():
        calls.append(1)

    runtime = Runtime(tick, interval_seconds=1, watchdog=watchdog)
    # Execute the same supervision path used by run() without blocking the test.
    try:
        runtime.tick()
    except Exception as exc:
        watchdog.record_failure(exc)
    else:
        watchdog.record_success()

    assert calls == [1]
    assert watchdog.status().healthy
    assert watchdog.status().last_tick_at.tzinfo == UTC
