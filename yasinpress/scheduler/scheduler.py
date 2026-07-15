"""Scheduler facade."""
from typing import Callable
from .queue import Job, JobQueue

class Scheduler:
    """Schedules named tasks."""
    def __init__(self, queue: JobQueue) -> None:
        self.queue = queue
    def schedule(self, name: str, task: Callable[[], None], priority: int = 100) -> None:
        """Schedule a task with priority."""
        self.queue.put(Job(priority, name, task))
