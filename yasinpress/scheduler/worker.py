"""Queue worker with explicit lifecycle tracking."""
from __future__ import annotations

from .jobs import JobRunner, new_job
from .persistence import InMemoryJobStore
from .queue import JobQueue
from .retry import RetryPolicy


class Worker:
    """Executes queued jobs while preserving the existing priority queue API."""

    def __init__(self, queue: JobQueue, retry: RetryPolicy | None = None, store: InMemoryJobStore | None = None) -> None:
        self.queue = queue
        self.retry = retry or RetryPolicy()
        self.store = store or InMemoryJobStore()

    def run_once(self):
        """Run one queued task and return its lifecycle snapshot."""
        queued = self.queue.get()
        lifecycle = new_job(queued.name)
        self.store.save(lifecycle)
        result = JobRunner(queued.task).run(lifecycle)
        self.store.save(result)
        return self.store.get(result.id)
