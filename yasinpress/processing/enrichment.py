from __future__ import annotations

from dataclasses import dataclass

from yasinpress.ai.safe import SafeAIEnricher
from yasinpress.database.models import Article


@dataclass(frozen=True)
class EnrichmentResult:
    article: Article
    ai_success: bool
    provider: str
    error: str | None = None


class ArticleEnricher:
    """Apply optional AI enrichment without destroying persisted article state."""

    def __init__(self, ai: SafeAIEnricher | None = None) -> None:
        self.ai = ai or SafeAIEnricher()

    def enrich(self, article: Article) -> EnrichmentResult:
        result = self.ai.enrich(article)
        if not result.success:
            return EnrichmentResult(article, False, result.provider, result.error)

        modified = result.title != article.title or result.content != article.content
        enriched = Article(
            id=article.id,
            title=result.title,
            url=article.url,
            content=result.content,
            source=article.source,
            published_at=article.published_at,
            category=article.category,
            event_id=article.event_id,
            received_at=article.received_at,
            lifecycle_state="processed",
            ai_state="rewritten" if modified else "unchanged",
            ai_error=None,
            ai_modified=modified,
        )
        return EnrichmentResult(enriched, True, result.provider)
