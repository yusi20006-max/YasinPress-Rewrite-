from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

from yasinpress.config.runtime import RuntimeConfig
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.fetch.feed import FeedFetcher
from yasinpress.health import check_database
from yasinpress.pipeline.application import YasinPressApplication
from yasinpress.publishing import Publisher
from yasinpress.publishing.eitaa import EitaaPublisher
from yasinpress.publishing.pwa import PWAPublisher
from yasinpress.publishing.reliability import RetryPolicy
from yasinpress.publishing.rss import RSSPublisher
from yasinpress.recovery import recover_jobs
from yasinpress.runtime import Runtime
from yasinpress.scheduler.application_job import PipelineJobFactory
from yasinpress.scheduler.queue import JobQueue
from yasinpress.scheduler.retry import RetryPolicy as JobRetryPolicy
from yasinpress.scheduler.scheduler import Scheduler
from yasinpress.scheduler.worker import Worker


class RuntimeBundle:
    def __init__(
        self,
        *,
        config: RuntimeConfig,
        database: SQLiteRepositories,
        application: YasinPressApplication,
        worker: Worker,
        jobs: PipelineJobFactory,
        fetcher: FeedFetcher,
        scheduler: Scheduler,
        runtime: Runtime,
    ) -> None:
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


def _configured_publishers(config: RuntimeConfig) -> tuple[Publisher, ...]:
    publishers: list[Publisher] = [
        PWAPublisher(
            output_path=config.pwa_output_path,
            title=config.pwa_title,
            home_page_url=config.pwa_home_page_url,
            feed_url=config.pwa_feed_url,
            max_items=config.max_feed_items,
        ),
        RSSPublisher(
            output_path=config.rss_output_path,
            title=config.rss_title,
            link=config.rss_link,
            feed_url=config.rss_feed_url,
            max_items=config.max_feed_items,
        ),
    ]
    if config.eitaa_token:
        publishers.append(
            EitaaPublisher(
                token=config.eitaa_token,
                channel=config.eitaa_channel,
                api_base=config.eitaa_api_base,
                timeout=config.request_timeout_seconds,
            )
        )
    return tuple(publishers)


def _feed_label(url: str) -> str:
    """Return a compact source label for terminal activity messages."""
    hostname = urlparse(url).hostname or url
    return hostname.removeprefix("www.")


def build_runtime(
    *, config: RuntimeConfig | None = None, ai=None, publishers: Iterable[Publisher] | None = None
) -> RuntimeBundle:
    cfg = config or RuntimeConfig.from_env()
    cfg.validate()
    database = SQLiteRepositories(cfg.database_path)
    health = check_database(database.connection)
    if not health.ok:
        database.close()
        raise RuntimeError(f"database readiness check failed: {health.message}")

    recover_jobs(database.jobs, database.jobs.all())
    configured = tuple(publishers) if publishers is not None else _configured_publishers(cfg)
    application = YasinPressApplication(
        source=cfg.feed_source,
        ai=ai,
        publishers=configured,
        repositories=database,
        retry_policy=RetryPolicy(max_attempts=cfg.max_job_attempts),
        max_article_age_hours=cfg.max_article_age_hours,
        max_publications_per_hour=cfg.max_publications_per_hour,
    )
    worker = Worker(retry=JobRetryPolicy(attempts=cfg.max_job_attempts), store=database.jobs)

    from yasinpress.publishing.queue_processor import PublicationQueueProcessor
    queue_processor = PublicationQueueProcessor(
        repositories=database,
        publishers=configured,
        max_global_per_hour=cfg.max_publications_per_hour,
    )

    def on_feed_received(source: str, count: int) -> None:
        print(f"{count} news received from {_feed_label(source)}", flush=True)

    jobs = PipelineJobFactory(application, worker, on_feed_received=on_feed_received)
    fetcher = FeedFetcher(timeout=cfg.request_timeout_seconds)
    scheduler = Scheduler(JobQueue())

    if cfg.feed_urls:

        def fetch_and_submit() -> None:
            jobs.submit_urls(cfg.feed_urls, fetcher=fetcher)

        scheduler.add_interval(
            "feed-fetch", timedelta(seconds=cfg.scheduler_interval_seconds), fetch_and_submit
        )

    def tick() -> None:
        scheduler.run_due()
        job = worker.run_once()

        # Run persistent publication queue processing cycle
        published_results = queue_processor.process_cycle()
        if published_results:
            success_count = sum(r.success for r in published_results)
            print(f"Persistent Queue Dispatch: processed {len(published_results)} jobs, {success_count} succeeded", flush=True)

        if job is None or job.status.value != "succeeded":
            return

        report = getattr(job, "result", None)
        if report is None:
            return
        processing = getattr(report, "processing", None)
        if processing is None:
            return

        publications = processing.publications
        now = datetime.now(UTC).astimezone()
        sent = publications.success_count
        already = processing.duplicate_count + publications.skipped_count
        print(
            f"[{now:%Y-%m-%d %H:%M:%S %Z}] Publishing report: "
            f"{report.received_count} received, "
            f"{sent} sent, "
            f"{already} already sent, "
            f"{publications.failure_count} failed, "
            f"{processing.queued_count} queued, "
            f"{processing.old_count} old (>{cfg.max_article_age_hours:g}h), "
            f"hourly limit={cfg.max_publications_per_hour}",
            flush=True,
        )

    runtime = Runtime(tick, interval_seconds=cfg.worker_interval_seconds)
    return RuntimeBundle(
        config=cfg,
        database=database,
        application=application,
        worker=worker,
        jobs=jobs,
        fetcher=fetcher,
        scheduler=scheduler,
        runtime=runtime,
    )
