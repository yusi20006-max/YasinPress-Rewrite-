from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from yasinpress.ai.base import AIProvider
from yasinpress.database.models import Article
from yasinpress.pipeline.dedup import unique_items
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

    def _enrich(self, article: Article) -> Article:
        if self.ai is None:
            return article
        if hasattr(self.ai, "enrich"):
            result = self.ai.enrich(article)
            if getattr(result, "success", False):
                return Article(
                    id=article.id, title=result.title, url=article.url,
                    content=result.content, source=article.source,
                    published_at=article.published_at, category=article.category,
                )
            return article
        rewrite = getattr(self.ai, "rewrite", None)
        if rewrite is not None:
            content = rewrite(article.content)
            return Article(
                id=article.id, title=article.title, url=article.url,
                content=content, source=article.source,
                published_at=article.published_at, category=article.category,
            )
        return article

    def process(self, items: Iterable[FeedItem]) -> ProcessingReport:
        result = self.pipeline.process(unique_items(items))
        articles = tuple(self._enrich(article) for article in result.articles)
        results: list[PublishResult] = []
        for article in articles:
            results.extend(self.publisher.publish(article).results)
        return ProcessingReport(
            PipelineResult(len(articles), result.rejected, articles),
            PublishReport(tuple(results)),
        )
