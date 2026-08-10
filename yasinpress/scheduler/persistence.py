from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from yasinpress.scheduler.jobs import JobExecution, JobStatus


@dataclass(frozen=True)
class JobSnapshot:
    id: str
    name: str
    status: JobStatus
    attempts: int
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None


class InMemoryJobStore:
    """Persistence boundary for scheduler state."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobSnapshot] = {}

    def save(self, job: JobExecution) -> JobSnapshot:
        snapshot = JobSnapshot(job.id, job.name, job.status, job.attempts, job.created_at, job.started_at, job.finished_at, job.error)
        self._jobs[job.id] = snapshot
        return snapshot

    def get(self, job_id: str) -> JobSnapshot | None:
        return self._jobs.get(job_id)

    def all(self) -> tuple[JobSnapshot, ...]:
        return tuple(self._jobs.values())
