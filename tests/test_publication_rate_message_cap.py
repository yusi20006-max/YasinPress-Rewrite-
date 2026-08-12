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
        article = Article(
            id="article-1",
            title="خبر",
            url="https://example.com/1",
            content="متن",
            source="bbc",
            published_at=datetime.now(UTC),
        )
        repo.articles.save(article)
        repo.publication_queue.add_job(
            PublicationJob("article-1:eitaa", "article-1", "eitaa", "pending", 10, "normal", "bbc")
        )
        repo.publication_queue.add_job(
            PublicationJob("article-1:pwa", "article-1", "pwa", "pending", 10, "normal", "bbc")
        )

        eitaa = Publisher("eitaa")
        pwa = Publisher("pwa")
        processor = PublicationQueueProcessor(
            repo, [eitaa, pwa], max_global_per_hour=1, max_source_per_hour=5
        )

        results = processor.process_cycle(datetime.now(UTC))

        assert len([result for result in results if result.success]) == 1
        assert eitaa.calls + pwa.calls == 1
    finally:
        repo.close()
