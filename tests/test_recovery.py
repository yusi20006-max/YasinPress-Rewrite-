import sqlite3

from yasinpress.database.jobs import SQLiteJobRepository
from yasinpress.recovery import recover_jobs
from yasinpress.scheduler.jobs import JobStatus, new_job


def test_recovery_requeues_interrupted_jobs():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    repo = SQLiteJobRepository(conn)
    job = new_job("feed")
    job.status = JobStatus.RUNNING
    repo.save(job)
    report = recover_jobs(repo, [repo.get(job.id)])
    assert report.recovered == 1
    assert repo.get(job.id).status is JobStatus.PENDING
