from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from yasinpress.database.jobs import SQLiteJobRepository
from yasinpress.scheduler.jobs import JobStatus


@dataclass(frozen=True)
class RecoveryReport:
    recovered: int
    skipped: int


def recover_jobs(repository: SQLiteJobRepository, jobs: Iterable) -> RecoveryReport:
    recovered = skipped = 0
    for job in jobs:
        if job.status is not JobStatus.RUNNING:
            skipped += 1
            continue
        job.status = JobStatus.PENDING
        job.started_at = None
        job.error = "recovered after interrupted runtime"
        repository.save(job)
        recovered += 1
    return RecoveryReport(recovered, skipped)
