from datetime import timedelta

from yasinpress.runtime_scheduler import RuntimeScheduler


def test_runtime_scheduler_composes_existing_scheduler_and_watchdog():
    calls = []
    runtime = RuntimeScheduler(lambda: calls.append("tick") or "ok", interval=timedelta(seconds=1))
    assert runtime.tick_once() == "ok"
    assert calls == ["tick"]
    assert runtime.watchdog.status().consecutive_failures == 0
    runtime.stop()
    assert runtime.tick_once() is None


def test_runtime_scheduler_can_run_bounded():
    calls = []
    runtime = RuntimeScheduler(lambda: calls.append(1), interval=timedelta(seconds=1))
    assert runtime.start(max_ticks=2) == 2
    assert len(calls) == 2
