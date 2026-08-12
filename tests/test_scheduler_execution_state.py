from datetime import UTC, datetime, timedelta

from yasinpress.scheduler.scheduler import Scheduler


def test_run_due_returns_completed_execution_state():
    current = datetime(2026, 1, 1, tzinfo=UTC)
    scheduler = Scheduler(object(), now=lambda: current)
    scheduler.add_interval("fetch", timedelta(minutes=5), lambda: None)

    executions = scheduler.run_due()

    assert len(executions) == 1
    assert executions[0] is scheduler.executions[0]
    assert executions[0].success is True
    assert executions[0].error is None
