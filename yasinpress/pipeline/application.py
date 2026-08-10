from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from yasinpress.ai.base import AIProvider
from yasinpress.database.models import Article
from yasinpress.database.sqlite import SQLiteArticleRepository
from yasinpress.pipeline.service import ProcessingReport, ProcessingService
from yasinpress.publishing import Publisher


@dataclass(frozen=True)
class ApplicationReport:
    processing: ProcessingReport
    persisted_count: int


class YasinPressApplication:
    """Composition root for the feed-to-AI-to-persistence-to-publishing path."""

    def __init__(self, *, ai: AIProvider | None = None, publishers: Iterable[Publisher] = (), repository: SQLiteArticleRepository | None = None) -> None:
        self.repository = repository or SQLiteArticleRepository()
        self.processing = ProcessingService(ai=ai, publishers=publishers)

    def process_items(self, items: Iterable[object]) -> ApplicationReport:
        report = self.processing.process(items)
        self.repository.save_many(report.pipeline.articles)
        return ApplicationReport(report, len(report.pipeline.articles))

    def get_article(self, article_id: str) -> Article | None:
        return self.repository.get(article_id)

    def close(self) -> None:
        self.repository.close()
