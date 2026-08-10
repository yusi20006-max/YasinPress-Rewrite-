from yasinpress.scheduler.jobs import JobStatus, new_job
from yasinpress.scheduler.retry import RetryPolicy
from yasinpress.scheduler.worker import Worker


def test_worker_runs_submitted_job_and_persists_state():
    calls = []
    worker = Worker(retry=RetryPolicy(attempts=1))
    job = new_job("demo")
    worker.submit(job, lambda: calls.append("ok"))

    result = worker.run_once()

    assert result is job
    assert result.status is JobStatus.SUCCEEDED
    assert result.attempts == 1
    assert calls == ["ok"]
    assert worker.pending() == 0


def test_worker_retries_and_marks_failure():
    calls = []

    def fail():
        calls.append(1)
        raise RuntimeError("boom")

    worker = Worker(retry=RetryPolicy(attempts=2, delay=0))
    job = new_job("failing")
    worker.submit(job, fail)
    result = worker.run_once()

    assert result.status is JobStatus.FAILED
    assert result.attempts == 2
    assert result.error == "boom"
    assert len(calls) == 2


def test_empty_worker_is_non_blocking():
    worker = Worker()
    assert worker.run_once() is None
