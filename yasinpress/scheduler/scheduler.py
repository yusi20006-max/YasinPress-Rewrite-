from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from yasinpress.scheduler.jobs import JobExecution


@dataclass(frozen=True)
class Schedule:
    name: str
    interval: timedelta


@dataclass
class ScheduledTask:
    schedule: Schedule
    handler: Callable[[], None]
    next_run_at: datetime


class Scheduler:
    """Interval scheduler facade over the existing priority job queue."""

    def __init__(self, queue, *, now: Callable[[], datetime] | None = None) -> None:
        self.queue = queue
        self.now = now or (lambda: datetime.now(UTC))
        self.tasks: list[ScheduledTask] = []
        self.executions: list[JobExecution] = []

    def schedule(self, name: str, task: Callable[[], None], priority: int = 100) -> None:
        from .queue import Job

        self.queue.put(Job(priority, name, task))

    def add_interval(self, name: str, interval: timedelta, task: Callable[[], None]) -> None:
        if interval <= timedelta(0):
            raise ValueError("interval must be positive")
        self.tasks.append(ScheduledTask(Schedule(name, interval), task, self.now()))

    def run_due(self) -> tuple[JobExecution, ...]:
        current = self.now()
        created: list[JobExecution] = []
        for scheduled in self.tasks:
            if scheduled.next_run_at > current:
                continue
            execution = JobExecution(name=scheduled.schedule.name)
            self.executions.append(execution.run(scheduled.handler))
            created.append(execution)
            scheduled.next_run_at = current + scheduled.schedule.interval
        return tuple(created)

    def clear(self) -> None:
        self.tasks.clear()
        self.executions.clear()
