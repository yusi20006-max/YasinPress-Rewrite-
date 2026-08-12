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
    """Apply optional AI enrichment while preserving the explicit AI lifecycle contract."""

    def __init__(
        self,
        ai: SafeAIEnricher | None = None,
        *,
        fallback_on_error: bool = True,
    ) -> None:
        self.ai = ai
        self.fallback_on_error = fallback_on_error

    def enrich(self, article: Article) -> EnrichmentResult:
        # No configured provider is an intentional disabled state, not a failure.
        if self.ai is None:
            disabled = Article(
                id=article.id,
                title=article.title,
                url=article.url,
                content=article.content,
                source=article.source,
                published_at=article.published_at,
                category=article.category,
                event_id=article.event_id,
                received_at=article.received_at,
                lifecycle_state="processed",
                ai_state="disabled",
                ai_error=None,
                ai_modified=False,
                source_metadata=article.source_metadata,
            )
            return EnrichmentResult(disabled, False, "none")

        result = self.ai.enrich(article)
        if not result.success:
            state = "fallback_original" if self.fallback_on_error else "failed"
            fallback = Article(
                id=article.id,
                title=article.title,
                url=article.url,
                content=article.content,
                source=article.source,
                published_at=article.published_at,
                category=article.category,
                event_id=article.event_id,
                received_at=article.received_at,
                lifecycle_state="processed",
                ai_state=state,
                ai_error=result.error,
                ai_modified=False,
                source_metadata=article.source_metadata,
            )
            return EnrichmentResult(fallback, False, result.provider, result.error)

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
            ai_state="rewritten" if modified else "fallback_original",
            ai_error=None,
            ai_modified=modified,
            source_metadata=article.source_metadata,
        )
        return EnrichmentResult(enriched, True, result.provider)
