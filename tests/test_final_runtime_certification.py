from datetime import UTC, datetime, timedelta

from yasinpress.config.runtime import RuntimeConfig
from yasinpress.database.models import Article
from yasinpress.publishing import PublishResult
from yasinpress.runtime_factory import build_runtime
from yasinpress.sources.feed import FeedItem


class RecordingPublisher:
    name = "recording"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def publish(self, article: Article) -> PublishResult:
        self.calls.append(article.id)
        return PublishResult(True, self.name, external_id=f"test:{article.id}")


def test_final_runtime_tick_drains_persistent_queue_without_external_io(tmp_path, monkeypatch):
    monkeypatch.setenv("EXTERNAL_PUBLISH_DISABLED", "true")
    publisher = RecordingPublisher()
    config = RuntimeConfig(
        database_path=str(tmp_path / "press.db"),
        worker_interval_seconds=0.01,
        scheduler_interval_seconds=60.0,
        feed_urls=(),
        max_publications_per_hour=10,
        max_source_publications_per_hour=5,
        max_article_age_hours=12.0,
    )
    bundle = build_runtime(config=config, publishers=[publisher])
    try:
        now = datetime.now(UTC)
        report = bundle.application.process_items(
            [FeedItem("runtime certification", "https://example.test/news/1", "body", now)]
        )
        article_id = report.processing.pipeline.articles[0].id

        assert bundle.worker.pending() == 0
        assert bundle.application.queue_metrics()["queue_depth"] == 1

        bundle.runtime.tick()

        assert publisher.calls == [article_id]
        assert bundle.worker.pending() == 0
        assert bundle.application.queue_metrics()["queue_depth"] == 0
        assert bundle.application.queue_metrics()["published_last_hour"] == 1
        assert bundle.database.idempotency.seen(f"{article_id}:recording")
        assert len(bundle.database.delivery_history.for_article(article_id)) == 1

        bundle.runtime.tick()
        assert publisher.calls == [article_id]
        assert len(bundle.database.delivery_history.for_article(article_id)) == 1
    finally:
        bundle.close()


def test_final_runtime_respects_freshness_before_persistent_enqueue(tmp_path):
    publisher = RecordingPublisher()
    config = RuntimeConfig(
        database_path=str(tmp_path / "press.db"),
        worker_interval_seconds=0.01,
        scheduler_interval_seconds=60.0,
        feed_urls=(),
        max_article_age_hours=12.0,
    )
    bundle = build_runtime(config=config, publishers=[publisher])
    try:
        stale = datetime.now(UTC) - timedelta(hours=13)
        report = bundle.application.process_items(
            [FeedItem("stale", "https://example.test/news/stale", "body", stale)]
        )
        assert report.processing.old_count == 1
        assert report.processing.queued_count == 0
        assert bundle.application.queue_metrics()["queue_depth"] == 0

        bundle.runtime.tick()
        assert publisher.calls == []
    finally:
        bundle.close()
