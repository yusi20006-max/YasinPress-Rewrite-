from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.pipeline.application import YasinPressApplication
from yasinpress.publishing import PublishResult
from yasinpress.publishing.reliability import RetryPolicy
from yasinpress.sources.feed import FeedItem


class RecordingPublisher:
    name = "recording"

    def __init__(self):
        self.calls = 0

    def publish(self, article: Article) -> PublishResult:
        self.calls += 1
        return PublishResult(True, self.name, external_id=f"remote:{article.id}")


def test_full_feed_to_persistent_publish_and_idempotency(tmp_path):
    db = SQLiteRepositories(str(tmp_path / "press.db"))
    publisher = RecordingPublisher()
    app = YasinPressApplication(
        ai=None,
        publishers=[publisher],
        repositories=db,
        retry_policy=RetryPolicy(1, 0, 0),
    )
    now = datetime.now(UTC)
    item = FeedItem("title", "https://example.com/item", "body", now)

    first = app.process_items([item])

    from yasinpress.publishing.queue_processor import PublicationQueueProcessor

    processor = PublicationQueueProcessor(db, [publisher])
    processor.process_cycle()

    second = app.process_items([item])
    processor.process_cycle()

    assert first.persisted_count == 1
    assert second.persisted_count == 1
    assert publisher.calls == 1
    assert db.idempotency.seen(f"{first.processing.pipeline.articles[0].id}:recording")
    assert len(db.delivery_history.for_article(first.processing.pipeline.articles[0].id)) == 1
    app.close()
