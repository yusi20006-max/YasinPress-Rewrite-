from __future__ import annotations

from dataclasses import dataclass

from yasinpress.ai.safe import SafeAIEnricher
from yasinpress.database.models import Article


@dataclass(frozen=True)
class EnrichmentResult:
    """Result of optional AI enrichment."""

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
        """Enrich an article without allowing AI failures to stop processing."""
        if self.ai is None:
            return EnrichmentResult(
                self._with_ai(article, ai_state="disabled", ai_modified=False),
                False,
                "none",
            )

        result = self.ai.enrich(article)
        if not result.success:
            state = "fallback_original" if self.fallback_on_error else "failed"
            return EnrichmentResult(
                self._with_ai(
                    article,
                    ai_state=state,
                    ai_error=result.error,
                    ai_modified=False,
                ),
                False,
                result.provider,
                result.error,
            )

        title = result.title or article.title
        content = result.content or article.content
        modified = title != article.title or content != article.content
        metadata = dict(article.source_metadata or {}) if isinstance(article.source_metadata, dict) else {}
        metadata.update(result.metadata)
        metadata["ai_provider"] = result.provider
        metadata["ai_breaking"] = result.breaking
        if result.summary is not None:
            metadata["ai_summary"] = result.summary
        if result.category is not None:
            metadata["ai_category"] = result.category
        if result.priority is not None:
            metadata["ai_priority"] = result.priority

        enriched = Article(
            id=article.id,
            title=title,
            url=article.url,
            content=content,
            source=article.source,
            published_at=article.published_at,
            category=result.category or article.category,
            event_id=article.event_id,
            received_at=article.received_at,
            lifecycle_state="processed",
            ai_state="rewritten" if modified else "fallback_original",
            ai_error=None,
            ai_modified=modified,
            source_metadata=metadata,
        )
        return EnrichmentResult(enriched, True, result.provider)

    @staticmethod
    def _with_ai(
        article: Article,
        *,
        ai_state: str,
        ai_modified: bool,
        ai_error: str | None = None,
    ) -> Article:
        """Return a lifecycle-safe Article copy with unchanged provenance."""
        return Article(
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
            ai_state=ai_state,
            ai_error=ai_error,
            ai_modified=ai_modified,
            source_metadata=article.source_metadata,
        )
