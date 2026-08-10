from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from yasinpress.database.models import Article
from yasinpress.database.repositories import ArticleRepository
from yasinpress.processing.breaking import BreakingResult, detect_breaking
from yasinpress.processing.cleaner import clean_html
from yasinpress.processing.classifier import classify
from yasinpress.processing.duplicates import DuplicateDetector
from yasinpress.processing.freshness import is_fresh
from yasinpress.processing.priority import PriorityResult, calculate_priority
from yasinpress.processing.validator import validate_article
from yasinpress.sources.feed import FeedItem
from yasinpress.processing.normalization import normalize


@dataclass(frozen=True)
class ProcessedArticle:
    article: Article
    priority: PriorityResult
    breaking: BreakingResult


class ArticlePipeline:
    """Run the deterministic article-processing stages in one place."""

    def __init__(self, repository: ArticleRepository, *, max_age: timedelta = timedelta(hours=24)) -> None:
        self.repository = repository
        self.max_age = max_age
        self.duplicates = DuplicateDetector(repository)

    def process(self, item: FeedItem, *, source: str) -> ProcessedArticle | None:
        article = normalize(item, source)
        if not is_fresh(article.published_at, max_age=self.max_age):
            return None
        if self.duplicates.is_duplicate(article):
            return None

        article = Article(
            id=article.id,
            title=clean_html(article.title),
            url=article.url,
            content=clean_html(article.content),
            source=article.source,
            published_at=article.published_at,
            category=classify(article.title, article.content),
        )
        validate_article(article)
        priority = calculate_priority(article.title, article.content)
        breaking = detect_breaking(article.title, article.content)
        self.repository.save(article)
        return ProcessedArticle(article=article, priority=priority, breaking=breaking)
