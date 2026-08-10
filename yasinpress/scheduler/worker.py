"""Queue worker with lifecycle tracking, retries and persistent state."""
from __future__ import annotations

from queue import Empty
from typing import Callable

from .jobs import Job as LifecycleJob, JobStatus
from .persistence import InMemoryJobStore
from .queue import Job as QueuedJob, JobQueue
from .retry import RetryPolicy


class Worker:
    """Executes queued tasks and persists their lifecycle snapshots."""

    def __init__(self, queue: JobQueue | None = None, retry: RetryPolicy | None = None, store=None) -> None:
        self.queue = queue or JobQueue()
        self.retry = retry or RetryPolicy()
        self.store = store or InMemoryJobStore()

    def submit(self, job: LifecycleJob, handler: Callable[[], object], *, priority: int = 0) -> LifecycleJob:
        self.store.save(job)
        self.queue.put(QueuedJob(priority, job.name, lambda: handler()))
        return job

    def run_once(self) -> LifecycleJob | None:
        try:
            queued = self.queue._queue.get_nowait()
        except Empty:
            return None

        # The queue stores executable tasks; lifecycle identity is recovered from the name.
        # For submitted jobs, _pending maps the task back to its lifecycle object.
        lifecycle = self._pending.pop(id(queued.task), None) if hasattr(self, "_pending") else None
        if lifecycle is None:
            lifecycle = LifecycleJob(id=queued.name, name=queued.name)

        lifecycle.status = JobStatus.RUNNING
        lifecycle.started_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        self.store.save(lifecycle)
        last_error: Exception | None = None
        for _ in range(self.retry.attempts):
            lifecycle.attempts += 1
            try:
                queued.task()
            except Exception as exc:
                last_error = exc
                if lifecycle.attempts < self.retry.attempts:
                    import time
                    time.sleep(self.retry.delay * (2 ** (lifecycle.attempts - 1)))
                    continue
                lifecycle.status = JobStatus.FAILED
                lifecycle.error = str(exc)
            else:
                lifecycle.status = JobStatus.SUCCEEDED
                lifecycle.error = None
                break
        lifecycle.finished_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        self.store.save(lifecycle)
        return lifecycle

    def run_all(self) -> tuple[LifecycleJob, ...]:
        results: list[LifecycleJob] = []
        while True:
            result = self.run_once()
            if result is None:
                return tuple(results)
            results.append(result)

    def pending(self) -> int:
        return self.queue._queue.qsize()
