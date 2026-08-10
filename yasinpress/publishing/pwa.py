from __future__ import annotations

import json

from yasinpress.database.models import Article
from yasinpress.publishing import PublishResult, Publisher


class PWAPublisher(Publisher):
    """Produce a JSON delivery payload suitable for a YasinPress PWA/API layer."""

    def __init__(self, *, endpoint: str = "pwa") -> None:
        self.endpoint = endpoint

    @property
    def name(self) -> str:
        return "pwa"

    def render(self, article: Article) -> str:
        payload = {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "content": article.content,
            "source": article.source,
            "published_at": article.published_at.isoformat(),
            "category": article.category,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def publish(self, article: Article) -> PublishResult:
        self.render(article)
        return PublishResult(True, self.name, external_id=article.id)
