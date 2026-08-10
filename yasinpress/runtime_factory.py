from __future__ import annotations

from typing import Iterable

from yasinpress.config.runtime import RuntimeConfig
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.fetch.feed import FeedFetcher
from yasinpress.pipeline.application import YasinPressApplication
from yasinpress.publishing import Publisher
from yasinpress.runtime import Runtime
from yasinpress.scheduler.application_job import PipelineJobFactory
from yasinpress.scheduler.worker import Worker


class RuntimeBundle:
    def __init__(self, *, config: RuntimeConfig, database: SQLiteRepositories, application: YasinPressApplication,
                 worker: Worker, jobs: PipelineJobFactory, fetcher: FeedFetcher, runtime: Runtime) -> None:
        self.config = config
        self.database = database
        self.application = application
        self.worker = worker
        self.jobs = jobs
        self.fetcher = fetcher
        self.runtime = runtime

    def close(self) -> None:
        self.runtime.close()
        self.database.close()


def build_runtime(*, config: RuntimeConfig | None = None, ai=None,
                  publishers: Iterable[Publisher] = ()) -> RuntimeBundle:
    cfg = config or RuntimeConfig.from_env()
    cfg.validate()
    database = SQLiteRepositories(cfg.database_path)
    application = YasinPressApplication(source=cfg.feed_source, ai=ai, publishers=publishers, repositories=database)
    worker = Worker()
    jobs = PipelineJobFactory(application, worker)
    fetcher = FeedFetcher(timeout=cfg.request_timeout_seconds)
    runtime = Runtime(worker.run_once, interval_seconds=cfg.worker_interval_seconds)
    return RuntimeBundle(config=cfg, database=database, application=application, worker=worker,
                         jobs=jobs, fetcher=fetcher, runtime=runtime)
