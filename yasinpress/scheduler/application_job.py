from __future__ import annotations

from typing import Iterable

from yasinpress.pipeline.application import ApplicationReport, YasinPressApplication
from yasinpress.scheduler.jobs import Job
from yasinpress.scheduler.worker import Worker


class PipelineJobFactory:
    """Turns fetched feed items into executable scheduler jobs."""

    def __init__(self, app: YasinPressApplication, worker: Worker | None = None) -> None:
        self.app = app
        self.worker = worker or Worker()

    def submit(self, items: Iterable[object]) -> Job:
        materialized = tuple(items)
        from yasinpress.scheduler.jobs import new_job
        job = new_job("process-feed")
        self.worker.submit(job, lambda: self.app.process_items(materialized))
        return job

    def run_once(self) -> Job | None:
        return self.worker.run_once()

    def run_all(self) -> tuple[Job, ...]:
        return self.worker.run_all()
