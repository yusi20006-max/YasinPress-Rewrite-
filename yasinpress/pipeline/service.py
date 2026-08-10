from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from yasinpress.ai.base import AIProvider
from yasinpress.database.models import Article
from yasinpress.pipeline.runtime import ArticlePipeline, PipelineResult
from yasinpress.publishing import PublishResult, Publisher
from yasinpress.publishing.orchestrator import PublishReport, PublishingOrchestrator
from yasinpress.publishing.reliability import RetryPolicy
from yasinpress.sources.feed import FeedItem


@dataclass(frozen=True)
class ProcessingReport:
    pipeline: PipelineResult
    publications: PublishReport


class ProcessingService:
    """Application service joining deterministic processing, optional AI, and publishing."""

    def __init__(self, *, source: str, ai: AIProvider | None = None,
                 publishers: Iterable[Publisher] = (), history=None, idempotency=None,
                 retry_policy: RetryPolicy | None = None) -> None:
        self.ai = ai
        self.pipeline = ArticlePipeline(source)
        self.publisher = PublishingOrchestrator(
            tuple(publishers), retry_policy=retry_policy,
            history=history, idempotency=idempotency,
        )

    def process(self, items: Iterable[FeedItem]) -> ProcessingReport:
        result = self.pipeline.process(items)
        articles: list[Article] = []
        for article in result.articles:
            if self.ai is None:
                articles.append(article)
                continue
            enriched = self.ai.enrich(article)
            if enriched.success:
                articles.append(Article(id=article.id, title=enriched.title, url=article.url,
                                        content=enriched.content, source=article.source,
                                        published_at=article.published_at, category=article.category))
            else:
                articles.append(article)

        results: list[PublishResult] = []
        for article in articles:
            results.extend(self.publisher.publish(article).results)
        return ProcessingReport(PipelineResult(len(articles), result.rejected, tuple(articles)), PublishReport(tuple(results)))
