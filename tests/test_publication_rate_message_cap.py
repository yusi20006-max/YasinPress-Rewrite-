from datetime import UTC, datetime

from yasinpress.database.models import Article, PublicationJob
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.history import DeliveryRecord
from yasinpress.publishing.queue_processor import PublicationQueueProcessor


class Publisher:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    def publish(self, article: Article) -> PublishResult:
        self.calls += 1
        return PublishResult(True, self.name, external_id=f"{self.name}:{article.id}")


def add_job(repo, article_id: str, destination: str, source: str, priority: int = 10) -> None:
    repo.publication_queue.add_job(
        PublicationJob(
            f"{article_id}:{destination}",
            article_id,
            destination,
            "pending",
            priority,
            "breaking" if priority == 40 else "normal",
            source,
        )
    )


def test_global_cap_counts_unique_articles_and_allows_destination_fanout() -> None:
    repo = SQLiteRepositories(":memory:")
    try:
        now = datetime.now(UTC)
        publishers = [Publisher("eitaa"), Publisher("pwa"), Publisher("rss")]
        for index in range(32):
            article_id = f"article-{index}"
            repo.articles.save(Article(id=article_id, title="خبر", url=f"https://example.com/{index}", content="متن", source=f"source-{index}", published_at=now))
            for publisher in publishers:
                add_job(repo, article_id, publisher.name, f"source-{index}")

        processor = PublicationQueueProcessor(repo, publishers, max_global_per_hour=30, max_source_per_hour=5)
        results = processor.process_cycle(now)
        successes = [result for result in results if result.success]
        unique_articles = {record.article_id for record in repo.delivery_history.all() if record.success}

        assert len(unique_articles) == 30
        assert len(successes) == 90
        assert all(publisher.calls == 30 for publisher in publishers)
    finally:
        repo.close()


def test_per_source_cap_limits_each_source_to_five_unique_articles_per_hour() -> None:
    repo = SQLiteRepositories(":memory:")
    try:
        now = datetime.now(UTC)
        publisher = Publisher("eitaa")
        for index in range(8):
            article_id = f"article-{index}"
            repo.articles.save(Article(id=article_id, title="خبر", url=f"https://example.com/{index}", content="متن", source="bbc", published_at=now))
            add_job(repo, article_id, "eitaa", "bbc")

        processor = PublicationQueueProcessor(repo, [publisher], max_global_per_hour=30, max_source_per_hour=5)
        results = processor.process_cycle(now)
        successes = [result for result in results if result.success]
        unique_source_articles = {record.article_id for record in repo.delivery_history.all() if record.success}

        assert len(successes) == 5
        assert len(unique_source_articles) == 5
        assert publisher.calls == 5
    finally:
        repo.close()


def test_recently_published_article_can_finish_remaining_destination_fanout() -> None:
    repo = SQLiteRepositories(":memory:")
    try:
        now = datetime.now(UTC)
        publishers = [Publisher("eitaa"), Publisher("pwa"), Publisher("rss")]
        article_id = "article-existing"
        repo.articles.save(Article(id=article_id, title="خبر", url="https://example.com/existing", content="متن", source="bbc", published_at=now))
        add_job(repo, article_id, "eitaa", "bbc")
        add_job(repo, article_id, "pwa", "bbc")
        add_job(repo, article_id, "rss", "bbc")
        repo.delivery_history.add(DeliveryRecord(article_id=article_id, destination="eitaa", success=True, attempts=1, external_id="eitaa:article-existing", created_at=now))

        processor = PublicationQueueProcessor(repo, publishers, max_global_per_hour=1, max_source_per_hour=1)
        results = processor.process_cycle(now)

        assert sum(result.success for result in results) == 2
        assert {publisher.name: publisher.calls for publisher in publishers} == {"eitaa": 0, "pwa": 1, "rss": 1}
    finally:
        repo.close()
