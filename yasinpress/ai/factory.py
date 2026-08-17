from __future__ import annotations

from typing import Any

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.ai.config import AIConfig
from yasinpress.ai.openai_compatible import OpenAICompatibleProvider
from yasinpress.ai.resilient import AIResiliencePolicy, ResilientAIProvider
from yasinpress.ai.yasin_ai import YasinAIProvider
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
    """Build the configured provider behind the YasinPress AI boundary."""
    if not config.usable():
        return NoOpAIProvider()

    if config.provider == "yasin-ai":
        try:
            from yasinai.services import GenerationService
        except ImportError:
            return NoOpAIProvider()
        return ResilientAIProvider(
            YasinAIProvider(GenerationService(), model=config.model),
            AIResiliencePolicy(timeout_seconds=config.timeout_seconds, max_attempts=2),
        )

    if client is None:
        return NoOpAIProvider()
    provider = OpenAICompatibleProvider(client, model=config.model or "")
    return ResilientAIProvider(
        provider,
        AIResiliencePolicy(timeout_seconds=config.timeout_seconds, max_attempts=2),
    )
