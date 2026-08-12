from datetime import UTC, datetime, timedelta

from yasinpress.scheduler.scheduler import Scheduler


def test_failed_interval_task_is_recorded_and_scheduler_continues():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    calls = []

    def failing_task():
        calls.append("failed")
        raise RuntimeError("temporary failure")

    scheduler = Scheduler(object(), now=lambda: now)
    scheduler.add_interval("unstable", timedelta(minutes=1), failing_task)

    first = scheduler.run_due()
    assert first[0].status.value == "failed"
    assert "temporary failure" in (first[0].error or "")
    assert calls == ["failed"]

    # A failed task must remain schedulable rather than poisoning Scheduler state.
    scheduler.tasks[0].next_run_at = now
    calls.append("marker")
    second = scheduler.run_due()
    assert second[0].status.value == "failed"
    assert len(scheduler.executions) == 2
