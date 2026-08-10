"""Queue worker with explicit job lifecycle and storage boundary."""
from __future__ import annotations

from .jobs import Job, JobRunner
from .queue import JobQueue
from .retry import RetryPolicy
from .store import InMemoryJobStore, JobStore


class Worker:
    """Executes queued jobs while preserving the existing queue API."""

    def __init__(self, queue: JobQueue, retry: RetryPolicy | None = None, store: JobStore | None = None) -> None:
        self.queue = queue
        self.retry = retry or RetryPolicy()
        self.store = store or InMemoryJobStore()

    def run_once(self) -> Job | None:
        """Run one queued job and return its lifecycle record when available."""
        job = self.queue.get()
        if job is None:
            return None
        lifecycle = Job(id=str(job.id), name=getattr(job, "name", "queued"))
        self.store.save(lifecycle)
        result = JobRunner(job.task).run(lifecycle)
        self.store.save(result)
        return result
