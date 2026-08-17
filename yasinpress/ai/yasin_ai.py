from __future__ import annotations

import json
import re
from typing import Any

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.database.models import Article


class YasinAIProvider(AIProvider):
    """YasinPress adapter for the versioned Yasin-AI generation contract.

    YasinPress owns article/domain rules and publishing. Yasin-AI owns model
    routing and provider execution. No provider SDKs or private Yasin-AI
    modules are imported here.
    """

    def __init__(self, service: Any, *, model: str | None = None) -> None:
        self.service = service
        self.model = model

    @property
    def name(self) -> str:
        return "yasin-ai"

    def enrich(self, article: Article) -> AIResult:
        from yasinai.contracts import GenerationRequest

        prompt = (
            "Analyze this Persian news article and return ONLY a JSON object with "
            "the keys title, content, summary, category, priority, breaking. "
            "Rewrite concisely without inventing facts. Keep title and content in Persian. "
            "priority must be one of low, normal, high, critical; breaking must be boolean.\n\n"
            f"TITLE:\n{article.title}\n\nCONTENT:\n{article.content}"
        )
        request = GenerationRequest(
            prompt=prompt,
            model=self.model,
            max_tokens=2048,
            temperature=0.2,
            system_prompt=(
                "You are the canonical Yasin-AI news intelligence capability. "
                "Return valid JSON only. Never invent facts."
            ),
            metadata={"consumer": "yasinpress", "article_id": article.id},
        )
        result = self.service.generate(request)
        if not result.success:
            return AIResult(
                title=article.title,
                content=article.content,
                provider=self.name,
                success=False,
                error=result.error or "Yasin-AI generation failed",
                metadata={"yasin_ai_version": "1.1.4", "capability": "generation"},
            )

        payload = self._parse_json(result.text)
        if payload is None:
            return AIResult(
                title=article.title,
                content=article.content,
                provider=self.name,
                success=False,
                error="Invalid Yasin-AI structured response",
                metadata={"yasin_ai_version": "1.1.4", "capability": "generation"},
            )

        title = self._text(payload.get("title")) or article.title
        content = self._text(payload.get("content")) or article.content
        summary = self._text(payload.get("summary"))
        category = self._text(payload.get("category"))
        priority = self._text(payload.get("priority"))
        breaking = bool(payload.get("breaking", False))
        metadata = {
            "yasin_ai_version": "1.1.4",
            "capability": "generation",
            "model": result.model,
            "provider": result.provider or self.name,
        }
        return AIResult(
            title=title,
            content=content,
            provider=result.provider or self.name,
            success=True,
            summary=summary,
            category=category,
            priority=priority,
            breaking=breaking,
            metadata=metadata,
        )

    @staticmethod
    def _text(value: object) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _parse_json(text: str) -> dict[str, object] | None:
        candidate = text.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL | re.IGNORECASE)
        if fenced:
            candidate = fenced.group(1).strip()
        try:
            value = json.loads(candidate)
        except (TypeError, ValueError):
            return None
        return value if isinstance(value, dict) else None
