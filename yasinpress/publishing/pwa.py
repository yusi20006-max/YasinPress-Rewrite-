from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult


class PWAPublisher(Publisher):
    """Publish articles to a persistent JSON Feed 1.1 document for the PWA layer."""

    def __init__(
        self,
        *,
        endpoint: str = "pwa",
        output_path: str | os.PathLike[str] | None = None,
        title: str = "YasinPress",
        home_page_url: str = "",
        feed_url: str = "",
        language: str = "fa",
        max_items: int = 100,
    ) -> None:
        self.endpoint = endpoint
        self.output_path = Path(output_path) if output_path else None
        self.title = title
        self.home_page_url = home_page_url
        self.feed_url = feed_url
        self.language = language
        self.max_items = max(1, max_items)

    @property
    def name(self) -> str:
        return "pwa"

    def _item(self, article: Article) -> dict[str, object]:
        item: dict[str, object] = {
            "id": article.id,
            "url": article.url,
            "title": article.title,
            "content_text": article.content,
            "date_published": article.published_at.isoformat(),
            "tags": [article.category] if article.category else [],
        }
        if article.ai_modified:
            item["date_modified"] = article.received_at.isoformat()
        if article.source:
            item["author"] = {"name": article.source}
        return item

    def render(self, article: Article) -> str:
        return json.dumps(self._item(article), ensure_ascii=False, sort_keys=True)

    def _feed(self, items: list[dict[str, object]]) -> dict[str, object]:
        feed: dict[str, object] = {
            "version": "https://jsonfeed.org/version/1.1",
            "title": self.title,
            "language": self.language,
            "items": items[: self.max_items],
        }
        if self.home_page_url:
            feed["home_page_url"] = self.home_page_url
        if self.feed_url:
            feed["feed_url"] = self.feed_url
        return feed

    def _write(self, items: list[dict[str, object]]) -> None:
        if self.output_path is None:
            return
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=self.output_path.parent, delete=False
        ) as handle:
            json.dump(self._feed(items), handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temporary = Path(handle.name)
        temporary.replace(self.output_path)

    def publish(self, article: Article) -> PublishResult:
        if self.output_path is None:
            return PublishResult(True, self.name, external_id=article.id)

        items: list[dict[str, object]] = []
        if self.output_path.exists():
            try:
                payload = json.loads(self.output_path.read_text(encoding="utf-8"))
                existing = payload.get("items", [])
                if isinstance(existing, list):
                    items = [item for item in existing if isinstance(item, dict)]
            except (OSError, ValueError, TypeError):
                items = []

        new_item = self._item(article)
        items = [item for item in items if str(item.get("id")) != article.id]
        items.insert(0, new_item)
        self._write(items)
        return PublishResult(True, self.name, external_id=article.id)
