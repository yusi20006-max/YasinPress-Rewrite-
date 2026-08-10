from __future__ import annotations

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.database.models import Article


class MockAIProvider(AIProvider):
    """Deterministic provider for tests and local pipeline development."""

    @property
    def name(self) -> str:
        return "mock"

    def enrich(self, article: Article) -> AIResult:
        return AIResult(
            title=article.title.strip(),
            content=article.content.strip(),
            provider=self.name,
        )


class FailingAIProvider(AIProvider):
    """Provider used to verify non-fatal AI failure handling."""

    @property
    def name(self) -> str:
        return "failing-mock"

    def enrich(self, article: Article) -> AIResult:
        raise RuntimeError("simulated AI provider failure")
