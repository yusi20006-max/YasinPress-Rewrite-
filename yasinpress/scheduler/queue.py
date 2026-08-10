"""Priority queue primitives."""
from dataclasses import dataclass, field
from queue import Empty, PriorityQueue
from typing import Callable


@dataclass(order=True)
class Job:
    """Queued unit of work."""
    priority: int
    name: str = field(compare=False)
    task: Callable[[], object] = field(compare=False)


class JobQueue:
    """Thread-safe priority job queue."""

    def __init__(self) -> None:
        self._queue: PriorityQueue[Job] = PriorityQueue()

    def put(self, job: Job) -> None:
        self._queue.put(job)

    def get(self) -> Job:
        return self._queue.get()

    def get_nowait(self) -> Job:
        return self._queue.get_nowait()

    def qsize(self) -> int:
        return self._queue.qsize()

    def empty(self) -> bool:
        return self._queue.empty()
