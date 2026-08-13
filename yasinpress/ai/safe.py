from __future__ import annotations

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.database.models import Article


class SafeAIEnricher:
    """Wrap an optional provider so AI failures never abort article processing."""

    def __init__(self, provider: AIProvider | None = None) -> None:
        self.provider = provider

    def enrich(self, article: Article) -> AIResult:
        """Return a structured result while containing every provider failure."""
        if self.provider is None:
            return AIResult(
                title=article.title,
                content=article.content,
                provider="none",
                success=False,
                error="AI provider unavailable",
            )
        try:
            result = self.provider.enrich(article)
            if result.title is None:
                result = AIResult(
                    title=article.title,
                    content=result.content or article.content,
                    provider=result.provider or self.provider.name,
                    success=result.success,
                    error=result.error,
                    summary=result.summary,
                    category=result.category,
                    priority=result.priority,
                    breaking=result.breaking,
                    metadata=result.metadata,
                )
            return result
        except Exception as exc:
            return AIResult(
                title=article.title,
                content=article.content,
                provider=self.provider.name,
                success=False,
                error=str(exc),
            )
