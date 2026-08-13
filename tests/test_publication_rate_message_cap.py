from collections import Counter
from datetime import UTC, datetime

from yasinpress.database.models import Article, PublicationJob
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.queue_processor import PublicationQueueProcessor


class Publisher:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    def publish(self, article: Article) -> PublishResult:
        self.calls += 1
        return PublishResult(True, self.name, external_id=f"{self.name}:{article.id}")


def test_global_cap_counts_publication_messages_not_unique_articles() -> None:
    repo = SQLiteRepositories(":memory:")
    try:
        now = datetime.now(UTC)
        publishers = [Publisher("eitaa")]
        for index in range(12):
            article_id = f"article-{index}"
            repo.articles.save(
                Article(
                    id=article_id,
                    title="خبر",
                    url=f"https://example.com/{index}",
                    content="متن",
                    source=f"source-{index}",
                    published_at=now,
                )
            )
            repo.publication_queue.add_job(
                PublicationJob(
                    f"{article_id}:eitaa",
                    article_id,
                    "eitaa",
                    "pending",
                    10,
                    "normal",
                    f"source-{index}",
                )
            )

        processor = PublicationQueueProcessor(
            repo, publishers, max_global_per_hour=10, max_source_per_hour=5
        )
        results = processor.process_cycle(now)

        assert sum(result.success for result in results) == 10
        assert publishers[0].calls == 10
    finally:
        repo.close()


def test_per_source_cap_limits_each_source_to_five_messages_per_hour() -> None:
    repo = SQLiteRepositories(":memory:")
    try:
        now = datetime.now(UTC)
        publishers = [Publisher("eitaa")]
        for index in range(8):
            article_id = f"article-{index}"
            repo.articles.save(
                Article(
                    id=article_id,
                    title="خبر",
                    url=f"https://example.com/{index}",
                    content="متن",
                    source="bbc",
                    published_at=now,
                )
            )
            repo.publication_queue.add_job(
                PublicationJob(
                    f"{article_id}:eitaa",
                    article_id,
                    "eitaa",
                    "pending",
                    10,
                    "normal",
                    "bbc",
                )
            )

        processor = PublicationQueueProcessor(
            repo, publishers, max_global_per_hour=10, max_source_per_hour=5
        )
        results = processor.process_cycle(now)

        assert sum(result.success for result in results) == 5
        assert publishers[0].calls == 5
        source_counts = Counter(
            record.article_id for record in repo.delivery_history.all() if record.success
        )
        assert len(source_counts) == 5
    finally:
        repo.close()
