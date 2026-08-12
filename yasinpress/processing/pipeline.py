from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from yasinpress.ai.safe import SafeAIEnricher
from yasinpress.database.models import Article
from yasinpress.database.repositories import ArticleRepository
from yasinpress.processing.breaking import BreakingResult, detect_breaking
from yasinpress.processing.classifier import classify
from yasinpress.processing.cleaner import clean_html
from yasinpress.processing.duplicates import DuplicateDetector
from yasinpress.processing.enrichment import ArticleEnricher
from yasinpress.processing.freshness import is_fresh
from yasinpress.processing.normalization import normalize
from yasinpress.processing.priority import PriorityResult, calculate_priority
from yasinpress.processing.validator import validate_article
from yasinpress.sources.feed import FeedItem


@dataclass(frozen=True)
class ProcessedArticle:
    article: Article
    priority: PriorityResult
    breaking: BreakingResult
    ai_success: bool = False
    ai_provider: str = "none"
    ai_error: str | None = None


class ArticlePipeline:
    """Run deterministic processing and optional fail-open AI enrichment."""

    def __init__(
        self,
        repository: ArticleRepository,
        *,
        max_age: timedelta = timedelta(hours=12),
        breaking_max_age: timedelta = timedelta(hours=24),
        allow_breaking_exemption: bool = True,
        ai: SafeAIEnricher | None = None,
    ) -> None:
        self.repository = repository
        self.max_age = max_age
        self.breaking_max_age = breaking_max_age
        self.allow_breaking_exemption = allow_breaking_exemption
        self.duplicates = DuplicateDetector(repository)
        self.enricher = ArticleEnricher(ai)

    def process(self, item: FeedItem, *, source: str) -> ProcessedArticle | None:
        article = normalize(item, source)

        # Detect breaking before freshness check to allow exemption
        breaking = detect_breaking(article.title, article.content)

        if not is_fresh(
            article.published_at,
            max_age=self.max_age,
            is_breaking=breaking.is_breaking,
            breaking_max_age=self.breaking_max_age,
            allow_breaking_exemption=self.allow_breaking_exemption,
        ):
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
            event_id=article.event_id,
            received_at=article.received_at,
            lifecycle_state="processed",
        )
        validate_article(article)
        priority = calculate_priority(article.title, article.content)

        enrichment = self.enricher.enrich(article)
        article = enrichment.article
        self.repository.save(article)
        return ProcessedArticle(
            article=article,
            priority=priority,
            breaking=breaking,
            ai_success=enrichment.ai_success,
            ai_provider=enrichment.provider,
            ai_error=enrichment.error,
        )
