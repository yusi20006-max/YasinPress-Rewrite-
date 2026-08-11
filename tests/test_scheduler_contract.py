from datetime import timedelta

from yasinpress.scheduler.jobs import JobExecution, JobStatus
from yasinpress.scheduler.queue import JobQueue
from yasinpress.scheduler.scheduler import Scheduler


def test_job_execution_success_and_failure():
    success = JobExecution(name="ok").run(lambda: None)
    assert success.status is JobStatus.SUCCEEDED
    assert success.started_at is not None
    assert success.finished_at is not None

    failure = JobExecution(name="bad").run(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert failure.status is JobStatus.FAILED
    assert failure.error == "boom"


def test_scheduler_runs_due_interval_task():
    queue = JobQueue()
    scheduler = Scheduler(queue)
    calls = []
    scheduler.add_interval("task", timedelta(seconds=1), lambda: calls.append("ran"))
    executions = scheduler.run_due()
    assert len(executions) == 1
    assert executions[0].status is JobStatus.SUCCEEDED
    assert calls == ["ran"]
