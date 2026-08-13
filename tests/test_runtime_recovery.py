
from yasinpress.runtime import Runtime
from yasinpress.watchdog import Watchdog


def test_runtime_recovery_hook_runs_after_bounded_failures(monkeypatch):
    events = []
    calls = 0

    def tick():
        nonlocal calls
        calls += 1
        if calls <= 3:
            raise RuntimeError("temporary")
        events.append("tick")
        runtime.stop()

    def recover():
        events.append("recover")

    runtime = Runtime(
        tick,
        interval_seconds=0.001,
        watchdog=Watchdog(stale_after=60),
        recover=recover,
        max_consecutive_failures=3,
    )
    runtime.run()
    assert events == ["recover", "tick"]


def test_runtime_rejects_invalid_failure_threshold():
    try:
        Runtime(lambda: None, max_consecutive_failures=0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
