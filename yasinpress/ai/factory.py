from __future__ import annotations

from typing import Any

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.ai.config import AIConfig
from yasinpress.ai.openai_compatible import OpenAICompatibleProvider
from yasinpress.database.models import Article


class NoOpAIProvider(AIProvider):
    @property
    def name(self) -> str:
        return "none"

    def enrich(self, article: Article) -> AIResult:
        return AIResult(
            article.title, article.content, self.name, success=False, error="AI disabled"
        )


def create_ai_provider(config: AIConfig, *, client: Any | None = None) -> AIProvider:
    """Build the configured provider without importing a concrete SDK at module import time."""
    if not config.usable() or client is None:
        return NoOpAIProvider()
    return OpenAICompatibleProvider(client, model=config.model)
