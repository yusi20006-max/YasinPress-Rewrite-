from datetime import UTC, datetime

from yasinpress.database.models import Article, PublicationJob
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.queue_processor import PublicationQueueProcessor


class CountingPublisher:
    name = "pwa"

    def __init__(self):
        self.calls = 0

    def publish(self, article):
        self.calls += 1
        return PublishResult(True, self.name, external_id=article.id)


def _enqueue(repo, article_id: str, source: str) -> None:
    repo.articles.save(
        Article(
            id=article_id,
            title=article_id,
            url=f"https://example.com/{article_id}",
            content="body",
            source=source,
            published_at=datetime.now(UTC),
        )
    )
    repo.publication_queue.add_job(
        PublicationJob(
            id=f"{article_id}:pwa",
            article_id=article_id,
            destination="pwa",
            status="pending",
            priority=10,
            priority_level="normal",
            source=source,
        )
    )


def test_default_global_publication_limit_is_ten_per_hour(tmp_path):
    repo = SQLiteRepositories(str(tmp_path / "limit.db"))
    for index in range(12):
        _enqueue(repo, f"article-{index}", f"source-{index}")

    publisher = CountingPublisher()
    processor = PublicationQueueProcessor(repo, [publisher])
    results = processor.process_cycle(datetime.now(UTC))

    assert len(results) == 10
    assert publisher.calls == 10


def test_retry_state_is_bounded_and_recoverable(tmp_path):
    repo = SQLiteRepositories(str(tmp_path / "retry.db"))
    _enqueue(repo, "retry-1", "source")
    job = repo.publication_queue.get_job("retry-1:pwa")
    assert job is not None
    job.status = "processing"
    job.attempts = 1
    job.lease_expires_at = datetime.now(UTC)
    repo.publication_queue.save_job(job)

    processor = PublicationQueueProcessor(repo, [], base_backoff_seconds=0)
    recovered = processor.recover_expired_leases(datetime.now(UTC))

    assert recovered == 1
    recovered_job = repo.publication_queue.get_job("retry-1:pwa")
    assert recovered_job is not None
    assert recovered_job.status == "retrying"
    assert recovered_job.lease_expires_at is None
    assert recovered_job.last_error == "Lease expired (worker crash recovery)"
