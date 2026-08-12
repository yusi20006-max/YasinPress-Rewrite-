from __future__ import annotations

from collections.abc import Iterable

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.database.models import Article


class FallbackAIProvider(AIProvider):
    """Try providers in deterministic order and fail open only after all fail."""

    def __init__(self, providers: Iterable[AIProvider]) -> None:
        self.providers = tuple(providers)
        if not self.providers:
            raise ValueError("at least one AI provider is required")

    @property
    def name(self) -> str:
        return "fallback"

    def enrich(self, article: Article) -> AIResult:
        errors: list[str] = []
        for provider in self.providers:
            try:
                result = provider.enrich(article)
            except Exception as exc:  # provider boundary
                errors.append(f"{provider.name}: {exc}")
                continue
            if result.success:
                return result
            errors.append(f"{provider.name}: {result.error or 'provider failed'}")
        return AIResult(article.title, article.content, "fallback", success=False, error="; ".join(errors))
