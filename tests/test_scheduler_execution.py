from datetime import UTC, datetime, timedelta

from yasinpress.scheduler.jobs import JobStatus
from yasinpress.scheduler.queue import JobQueue
from yasinpress.scheduler.scheduler import Scheduler


def test_interval_scheduler_runs_due_task_once():
    now = [datetime(2026, 1, 1, tzinfo=UTC)]
    calls = []
    scheduler = Scheduler(JobQueue(), now=lambda: now[0])
    scheduler.add_interval("feed", timedelta(minutes=5), lambda: calls.append("run"))
    results = scheduler.run_due()
    assert len(results) == 1
    assert results[0].status == JobStatus.SUCCEEDED
    assert calls == ["run"]
    assert scheduler.run_due() == ()


def test_interval_scheduler_records_failure():
    scheduler = Scheduler(JobQueue())
    scheduler.add_interval(
        "broken", timedelta(minutes=1), lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    result = scheduler.run_due()[0]
    assert result.status == JobStatus.FAILED
    assert result.error == "boom"
    assert result.attempts == 1
