from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import httpx

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.database.models import Article


class _HTTPChatCompletions:
    def __init__(self, *, base_url: str, api_key: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def create(self, *, model: str, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        payload = {"model": model, "messages": messages, **kwargs}
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices") or []
        if not choices or not isinstance(choices[0], dict):
            raise ValueError("OpenAI-compatible response contains no choices")
        message = choices[0].get("message") or {}
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=message.get("content")))],
        )


class _HTTPChat:
    def __init__(self, *, base_url: str, api_key: str, timeout_seconds: float) -> None:
        self.completions = _HTTPChatCompletions(
            base_url=base_url,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )


class HTTPXOpenAICompatibleClient:
    """Small dependency-free OpenAI-compatible client built on httpx."""

    def __init__(self, *, base_url: str, api_key: str, timeout_seconds: float) -> None:
        self.chat = _HTTPChat(
            base_url=base_url,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )


class OpenAICompatibleProvider(AIProvider):
    """Provider adapter for any OpenAI-compatible chat-completions endpoint."""

    def __init__(
        self, client: Any, *, model: str, provider_name: str = "openai-compatible"
    ) -> None:
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
