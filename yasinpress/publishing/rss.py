from __future__ import annotations

from email.utils import format_datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree.ElementTree import Element, SubElement, tostring

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult


class RSSPublisher(Publisher):
    """Publish articles to a persistent RSS 2.0 feed."""

    def __init__(
        self,
        *,
        feed_url: str = "",
        output_path: str | Path | None = None,
        title: str = "YasinPress",
        link: str = "",
        description: str = "YasinPress news feed",
        max_items: int = 100,
    ) -> None:
        self.feed_url = feed_url
        self.output_path = Path(output_path) if output_path else None
        self.title = title
        self.link = link
        self.description = description
        self.max_items = max(1, max_items)

    @property
    def name(self) -> str:
        return "rss"

    def _item(self, article: Article) -> Element:
        item = Element("item")
        SubElement(item, "title").text = article.title
        SubElement(item, "link").text = article.url
        SubElement(item, "guid", isPermaLink="true").text = article.url
        SubElement(item, "description").text = article.content
        SubElement(item, "pubDate").text = format_datetime(article.published_at)
        if article.category:
            SubElement(item, "category").text = article.category
        return item

    def render(self, article: Article) -> str:
        return tostring(self._item(article), encoding="unicode")

    def _feed(self, items: list[Element]) -> Element:
        rss = Element("rss", version="2.0")
        channel = SubElement(rss, "channel")
        SubElement(channel, "title").text = self.title
        SubElement(channel, "link").text = self.link or self.feed_url
        SubElement(channel, "description").text = self.description
        if self.feed_url:
            SubElement(channel, "atom:link", {
                "href": self.feed_url,
                "rel": "self",
                "type": "application/rss+xml",
            })
        for item in items[: self.max_items]:
            channel.append(item)
        return rss

    def _read_items(self) -> list[Element]:
        if self.output_path is None or not self.output_path.exists():
            return []
        try:
            from xml.etree.ElementTree import parse

            root = parse(self.output_path).getroot()
            channel = root.find("channel")
            if channel is None:
                return []
            return [item for item in channel.findall("item")]
        except (OSError, ValueError):
            return []

    def _write(self, items: list[Element]) -> None:
        if self.output_path is None:
            return
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = tostring(self._feed(items), encoding="unicode")
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=self.output_path.parent, delete=False
        ) as handle:
            handle.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            handle.write(payload)
            handle.write("\n")
            temporary = Path(handle.name)
        temporary.replace(self.output_path)

    def publish(self, article: Article) -> PublishResult:
        if self.output_path is None:
            return PublishResult(True, self.name, external_id=article.url)

        items = self._read_items()
        items = [item for item in items if item.findtext("guid") != article.url]
        items.insert(0, self._item(article))
        self._write(items)
        return PublishResult(True, self.name, external_id=article.url)
