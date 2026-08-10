from __future__ import annotations

from threading import Lock

from yasinpress.scheduler.jobs import Job


class JobStore:
    """Storage-neutral job store contract."""

    def save(self, job: Job) -> None:
        raise NotImplementedError

    def get(self, job_id: str) -> Job | None:
        raise NotImplementedError

    def all(self) -> tuple[Job, ...]:
        raise NotImplementedError


class InMemoryJobStore(JobStore):
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = Lock()

    def save(self, job: Job) -> None:
        with self._lock:
            self._jobs[job.id] = job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def all(self) -> tuple[Job, ...]:
        with self._lock:
            return tuple(self._jobs.values())
