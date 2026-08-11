"""Queue worker with lifecycle tracking, retries and persistent state."""
from __future__ import annotations

from datetime import UTC, datetime
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
        self._pending: dict[int, LifecycleJob] = {}

    def submit(self, job: LifecycleJob, handler: Callable[[], object], *, priority: int = 0) -> LifecycleJob:
        self.store.save(job)
        task = lambda: handler()
        self._pending[id(task)] = job
        self.queue.put(QueuedJob(priority, job.name, task))
        return job

    def run_once(self) -> LifecycleJob | None:
        try:
            queued = self.queue.get_nowait()
        except Empty:
            return None

        lifecycle = self._pending.pop(id(queued.task), None)
        if lifecycle is None:
            lifecycle = LifecycleJob(id=queued.name, name=queued.name)

        lifecycle.status = JobStatus.RUNNING
        lifecycle.started_at = datetime.now(UTC)
        self.store.save(lifecycle)

        for attempt in range(self.retry.attempts):
            lifecycle.attempts += 1
            try:
                queued.task()
            except Exception as exc:  # noqa: BLE001 - worker boundary records and retries task failures
                lifecycle.error = str(exc)
                if attempt + 1 < self.retry.attempts:
                    import time
                    time.sleep(self.retry.delay * (2 ** attempt))
                    continue
                lifecycle.status = JobStatus.FAILED
            else:
                lifecycle.status = JobStatus.SUCCEEDED
                lifecycle.error = None
                break

        lifecycle.finished_at = datetime.now(UTC)
        self.store.save(lifecycle)
        return lifecycle

    def run_all(self) -> tuple[LifecycleJob, ...]:
        results: list[LifecycleJob] = []
        while (result := self.run_once()) is not None:
            results.append(result)
        return tuple(results)

    def pending(self) -> int:
        return self.queue.qsize()
