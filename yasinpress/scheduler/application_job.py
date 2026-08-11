from __future__ import annotations

from collections.abc import Callable, Iterable

from yasinpress.fetch.feed import FeedFetcher
from yasinpress.pipeline.application import YasinPressApplication
from yasinpress.scheduler.jobs import Job
from yasinpress.scheduler.worker import Worker


class PipelineJobFactory:
    """Turns feed items or URLs into executable scheduler jobs."""

    def __init__(
        self,
        app: YasinPressApplication,
        worker: Worker | None = None,
        on_feed_received: Callable[[str, int], None] | None = None,
    ) -> None:
        self.app = app
        self.worker = worker or Worker()
        self.on_feed_received = on_feed_received

    def submit(self, items: Iterable[object]) -> Job:
        materialized = tuple(items)
        from yasinpress.scheduler.jobs import new_job

        job = new_job("process-feed")
        return self.worker.submit(job, lambda: self.app.process_items(materialized))

    def submit_urls(self, urls: tuple[str, ...], *, fetcher: FeedFetcher | None = None) -> Job:
        feed_fetcher = fetcher or FeedFetcher()
        from yasinpress.scheduler.jobs import new_job

        job = new_job("fetch-and-process-feeds")

        def execute() -> None:
            results = feed_fetcher.fetch_many(urls)
            total_received = 0
            for result in results:
                count = len(result.items)
                total_received += count
                if self.on_feed_received is not None:
                    self.on_feed_received(result.source, count)
            items = tuple(item for result in results for item in result.items)
            report = self.app.process_items(items)
            published = report.processing.publications.success_count
            failed = report.processing.publications.failure_count
            print(
                f"Publishing report: {published} sent, {failed} failed, "
                f"{report.persisted_count} processed ({total_received} received)",
                flush=True,
            )

        return self.worker.submit(job, execute)

    def run_once(self) -> Job | None:
        return self.worker.run_once()

    def run_all(self) -> tuple[Job, ...]:
        return self.worker.run_all()
