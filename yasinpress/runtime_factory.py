from __future__ import annotations

from datetime import timedelta
from typing import Iterable

from yasinpress.config.runtime import RuntimeConfig
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.fetch.feed import FeedFetcher
from yasinpress.health import check_database
from yasinpress.pipeline.application import YasinPressApplication
from yasinpress.publishing import Publisher
from yasinpress.publishing.reliability import RetryPolicy
from yasinpress.recovery import recover_jobs
from yasinpress.runtime import Runtime
from yasinpress.scheduler.application_job import PipelineJobFactory
from yasinpress.scheduler.queue import JobQueue
from yasinpress.scheduler.retry import RetryPolicy as JobRetryPolicy
from yasinpress.scheduler.scheduler import Scheduler
from yasinpress.scheduler.worker import Worker


class RuntimeBundle:
    def __init__(self, *, config: RuntimeConfig, database: SQLiteRepositories, application: YasinPressApplication,
                 worker: Worker, jobs: PipelineJobFactory, fetcher: FeedFetcher, scheduler: Scheduler, runtime: Runtime) -> None:
        self.config = config
        self.database = database
        self.application = application
        self.worker = worker
        self.jobs = jobs
        self.fetcher = fetcher
        self.scheduler = scheduler
        self.runtime = runtime

    def close(self) -> None:
        self.runtime.close()
        self.scheduler.clear()
        self.database.close()


def build_runtime(*, config: RuntimeConfig | None = None, ai=None,
                  publishers: Iterable[Publisher] = ()) -> RuntimeBundle:
    cfg = config or RuntimeConfig.from_env()
    cfg.validate()
    database = SQLiteRepositories(cfg.database_path)
    health = check_database(database.connection)
    if not health.ok:
        database.close()
        raise RuntimeError(f"database readiness check failed: {health.message}")

    recovery = recover_jobs(database.jobs, database.jobs.all())
    application = YasinPressApplication(
        source=cfg.feed_source, ai=ai, publishers=publishers,
        repositories=database,
        retry_policy=RetryPolicy(max_attempts=cfg.max_job_attempts),
    )
    worker = Worker(retry=JobRetryPolicy(attempts=cfg.max_job_attempts), store=database.jobs)
    jobs = PipelineJobFactory(application, worker)
    fetcher = FeedFetcher(timeout=cfg.request_timeout_seconds)
    scheduler = Scheduler(JobQueue())

    if cfg.feed_urls:
        def fetch_and_submit() -> None:
            jobs.submit_urls(cfg.feed_urls, fetcher=fetcher)
        scheduler.add_interval("feed-fetch", timedelta(seconds=cfg.scheduler_interval_seconds), fetch_and_submit)

    def tick() -> None:
        scheduler.run_due()
        worker.run_once()

    runtime = Runtime(tick, interval_seconds=cfg.worker_interval_seconds)
    return RuntimeBundle(config=cfg, database=database, application=application, worker=worker,
                         jobs=jobs, fetcher=fetcher, scheduler=scheduler, runtime=runtime)
