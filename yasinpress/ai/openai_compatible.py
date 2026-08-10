from __future__ import annotations

from typing import Any

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.database.models import Article


class OpenAICompatibleProvider(AIProvider):
    """Provider adapter for any OpenAI-compatible chat-completions endpoint."""

    def __init__(self, client: Any, *, model: str, provider_name: str = "openai-compatible") -> None:
        self.client = client
        self.model = model
        self._provider_name = provider_name

    @property
    def name(self) -> str:
        return self._provider_name

    def enrich(self, article: Article) -> AIResult:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Rewrite the article in clear, concise Persian. Preserve factual meaning and do not invent facts.",
                },
                {
                    "role": "user",
                    "content": f"Title:\n{article.title}\n\nContent:\n{article.content}",
                },
            ],
        )
        content = response.choices[0].message.content or article.content
        return AIResult(article.title, content.strip(), self.name)
