from datetime import UTC, datetime, timedelta

from yasinpress.database.models import Article, PublicationJob
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.queue_processor import PublicationQueueProcessor


class RecordingPublisher:
    name = "recording"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def publish(self, article: Article) -> PublishResult:
        self.calls.append(article.title)
        return PublishResult(True, self.name, external_id=article.id)


def _job(article_id: str, created_at: datetime) -> PublicationJob:
    return PublicationJob(
        id=f"{article_id}:recording",
        article_id=article_id,
        destination="recording",
        status="pending",
        priority=10,
        priority_level="normal",
        source="feed",
        created_at=created_at,
    )


def test_process_cycle_persists_publication_timestamp_and_is_idempotent(tmp_path):
    db = SQLiteRepositories(str(tmp_path / "press.db"))
    publisher = RecordingPublisher()
    processor = PublicationQueueProcessor(db, [publisher])
    published_at = datetime(2026, 1, 1, 12, tzinfo=UTC)

    article = Article(
        id="article-1",
        title="Original",
        url="https://example.com/1",
        content="body",
        source="feed",
        published_at=published_at,
        published_to_channel_at=None,
    )
    db.articles.save(article)
    db.publication_queue.add_job(_job(article.id, published_at))

    results = processor.process_cycle(now=published_at)

    assert len(results) == 1
    assert results[0].success is True
    saved = db.articles.get(article.id)
    assert saved is not None
    assert saved.published_to_channel_at == published_at
    assert len(db.delivery_history.for_article(article.id)) == 1

    processor.process_cycle(now=published_at + timedelta(seconds=1))
    assert publisher.calls == ["Original"]
    db.close()


def test_process_cycle_republishes_new_article_version(tmp_path):
    db = SQLiteRepositories(str(tmp_path / "press.db"))
    publisher = RecordingPublisher()
    processor = PublicationQueueProcessor(db, [publisher])
    first_time = datetime(2026, 1, 1, 12, tzinfo=UTC)
    second_time = first_time + timedelta(minutes=5)

    original = Article(
        id="article-2",
        title="Original",
        url="https://example.com/2",
        content="old",
        source="feed",
        published_at=first_time,
    )
    db.articles.save(original)
    db.publication_queue.add_job(_job(original.id, first_time))
    assert processor.process_cycle(now=first_time)[0].success

    updated = Article(
        id="article-2",
        title="Updated",
        url="https://example.com/2",
        content="new",
        source="feed",
        published_at=first_time,
        updated_at=second_time,
        published_to_channel_at=None,
    )
    db.articles.save(updated)
    db.publication_queue.add_job(_job(updated.id, second_time))

    results = processor.process_cycle(now=second_time)

    assert len(results) == 1
    assert results[0].success is True
    assert publisher.calls == ["Original", "Updated"]
    saved = db.articles.get(updated.id)
    assert saved is not None
    assert saved.published_to_channel_at == second_time
    db.close()
