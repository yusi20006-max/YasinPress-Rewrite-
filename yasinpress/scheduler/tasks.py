from __future__ import annotations

from collections.abc import Callable, Iterable

from yasinpress.pipeline.runtime import ArticlePipeline, PipelineResult
from yasinpress.scheduler.jobs import Job, JobRunner, new_job
from yasinpress.scheduler.store import InMemoryJobStore, JobStore
from yasinpress.sources.feed import FeedItem, parse_rss
from yasinpress.sources.fetcher import FetchEngine


def build_feed_job(
    source_name: str, url: str, handler: Callable[[str], None] | None = None
) -> tuple[Job, Callable[[], None]]:
    """Create a fetch/parse job; transport side effects remain injectable."""
    job = new_job(f"feed:{source_name}")
    fetcher = FetchEngine()

    def run() -> None:
        xml = fetcher.fetch(url)
        if handler:
            handler(xml)
        else:
            parse_rss(xml)

    return job, run


def build_pipeline_job(
    source_name: str,
    items: Iterable[FeedItem],
    sink: Callable[[PipelineResult], None],
    duplicate: Callable[[object], bool] | None = None,
) -> tuple[Job, Callable[[], None]]:
    """Create a deterministic pipeline execution job."""
    job = new_job(f"pipeline:{source_name}")
    materialized = tuple(items)
    pipeline = ArticlePipeline(source_name, duplicate=duplicate)

    def run() -> None:
        sink(pipeline.process(materialized))

    return job, run


def execute_job(job: Job, handler: Callable[[], None], store: JobStore | None = None) -> Job:
    """Execute and persist one application job."""
    store = store or InMemoryJobStore()
    store.save(job)
    result = JobRunner(handler).run(job)
    store.save(result)
    return result
