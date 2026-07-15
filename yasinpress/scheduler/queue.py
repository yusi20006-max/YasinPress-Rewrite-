"""Priority queue primitives."""
from dataclasses import dataclass, field
from queue import PriorityQueue
from typing import Callable

@dataclass(order=True)
class Job:
    """Queued unit of work."""
    priority: int
    name: str = field(compare=False)
    task: Callable[[], None] = field(compare=False)

class JobQueue:
    """Thread-safe priority job queue."""
    def __init__(self) -> None:
        self._queue: PriorityQueue[Job] = PriorityQueue()
    def put(self, job: Job) -> None:
        """Add a job."""
        self._queue.put(job)
    def get(self) -> Job:
        """Get the highest-priority job."""
        return self._queue.get()
