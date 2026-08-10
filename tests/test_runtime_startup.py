from yasinpress.config.runtime import RuntimeConfig
from yasinpress.runtime_factory import build_runtime
from yasinpress.scheduler.jobs import JobStatus, new_job


def test_startup_runs_recovery(tmp_path):
    path = str(tmp_path / "startup.db")
    cfg = RuntimeConfig(database_path=path)
    first = build_runtime(config=cfg)
    job = new_job("interrupted")
    job.status = JobStatus.RUNNING
    first.database.jobs.save(job)
    first.close()

    second = build_runtime(config=cfg)
    recovered = second.database.jobs.get(job.id)
    assert recovered is not None
    assert recovered.status is JobStatus.PENDING
    second.close()
