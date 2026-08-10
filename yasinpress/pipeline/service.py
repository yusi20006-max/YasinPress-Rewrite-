from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from yasinpress.ai.base import AIProvider
from yasinpress.database.models import Article
from yasinpress.pipeline.runtime import ArticlePipeline, PipelineResult
from yasinpress.publishing import Publisher
from yasinpress.publishing.orchestrator import PublishReport, PublishingOrchestrator


@dataclass(frozen=True)
class ProcessingReport:
    pipeline: PipelineResult
    publications: PublishReport | None


class ProcessingService:
    """Application service joining normalization, optional AI, persistence and publishing."""

    def __init__(self, *, ai: AIProvider | None = None, publishers: Iterable[Publisher] = ()) -> None:
        self.ai = ai
        self.pipeline = ArticlePipeline()
        self.publisher = PublishingOrchestrator(tuple(publishers))

    def process(self, items: Iterable[object]) -> ProcessingReport:
        result = self.pipeline.process(items)
        articles: list[Article] = []
        for article in result.articles:
            if self.ai is None:
                articles.append(article)
                continue
            enriched = self.ai.enrich(article)
            if enriched.success:
                articles.append(
                    Article(
                        id=article.id,
                        title=enriched.title,
                        url=article.url,
                        content=enriched.content,
                        source=article.source,
                        published_at=article.published_at,
                        category=article.category,
                    )
                )
            else:
                articles.append(article)
        publication = self.publisher.publish(articles[0]) if len(articles) == 1 else None
        return ProcessingReport(
            PipelineResult(tuple(articles), result.rejected, result.errors),
            publication,
        )
