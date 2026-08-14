from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from yasinpress.ai.base import AIProvider
from yasinpress.database.models import Article
from yasinpress.database.sqlite import SQLiteArticleRepository, SQLiteRepositories
from yasinpress.pipeline.service import ProcessingReport, ProcessingService
from yasinpress.publishing import Publisher, PublishResult
from yasinpress.publishing.queue import SQLitePublicationQueueEngine
from yasinpress.publishing.reliability import RetryPolicy
from yasinpress.sources.feed import FeedItem


@dataclass(frozen=True)
class ApplicationReport:
    processing: ProcessingReport
    persisted_count: int
    received_count: int = 0


class YasinPressApplication:
    """Composition root for feed → AI → persistence → queue → publishing."""

    def __init__(
        self,
        *,
        source: str = "rss",
        ai: AIProvider | None = None,
        publishers: Iterable[Publisher] = (),
        repository: SQLiteArticleRepository | None = None,
        repositories: SQLiteRepositories | None = None,
        retry_policy: RetryPolicy | None = None,
        max_article_age_hours: float = 12.0,
        max_publications_per_hour: int = 10,
    ) -> None:
        self.repositories = repositories
        self.publishers = tuple(publishers)
        if repository is not None:
            self.repository = repository
        elif repositories is not None:
            self.repository = repositories.articles
        else:
            self.repository = SQLiteArticleRepository()
        self.processing = ProcessingService(
            source=source,
            ai=ai,
            publishers=self.publishers,
            repository=self.repository,
            history=repositories.delivery_history if repositories else None,
            idempotency=repositories.idempotency if repositories else None,
            retry_policy=retry_policy,
            max_article_age_hours=max_article_age_hours,
            max_publications_per_hour=max_publications_per_hour,
            publication_queue=repositories.publication_queue if repositories else None,
        )

    def process_items(self, items: Iterable[FeedItem]) -> ApplicationReport:
        materialized = tuple(items)
        report = self.processing.process(materialized)
        self.repository.save_many(report.pipeline.articles)
        return ApplicationReport(
            report,
            len(report.pipeline.articles),
            received_count=len(materialized),
        )

    def publish_once(self) -> PublishResult | None:
        """Publish one durable queue job; never publishes from feed ingestion."""
        if self.repositories is None or not self.publishers:
            return None
        engine = SQLitePublicationQueueEngine(self.repositories.connection)
        publisher_map = {publisher.name: publisher for publisher in self.publishers}
        return engine.run_once(publisher_map, self.repository)

    def publish_pending(self, max_jobs: int = 10) -> tuple[PublishResult, ...]:
        """Drain at most ``max_jobs`` jobs through the durable worker path."""
        results: list[PublishResult] = []
        for _ in range(max(0, max_jobs)):
            result = self.publish_once()
            if result is None:
                break
            results.append(result)
        return tuple(results)

    def queue_metrics(self) -> dict[str, int]:
        if self.repositories is None:
            return {"queue_depth": 0, "published_last_hour": 0, "remaining_global_capacity": 0}
        return SQLitePublicationQueueEngine(self.repositories.connection).metrics()

    def get_article(self, article_id: str) -> Article | None:
        return self.repository.get(article_id)

    def close(self) -> None:
        if self.repositories is not None:
            self.repositories.close()
        else:
            self.repository.close()
