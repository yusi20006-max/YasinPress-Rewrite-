from __future__ import annotations

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.database.models import Article


class SafeAIEnricher:
    """Wrap an optional provider so AI failures never abort article processing."""

    def __init__(self, provider: AIProvider | None = None) -> None:
        self.provider = provider

    def enrich(self, article: Article) -> AIResult:
        if self.provider is None:
            return AIResult(article.title, article.content, "none", success=False, error="AI provider unavailable")
        try:
            return self.provider.enrich(article)
        except Exception as exc:  # noqa: BLE001 - provider boundary is intentionally non-fatal
            return AIResult(article.title, article.content, self.provider.name, success=False, error=str(exc))
