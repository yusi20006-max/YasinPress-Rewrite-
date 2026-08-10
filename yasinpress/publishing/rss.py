from __future__ import annotations

from email.utils import format_datetime
from xml.etree.ElementTree import Element, SubElement, tostring

from yasinpress.database.models import Article
from yasinpress.publishing import PublishResult, Publisher


class RSSPublisher(Publisher):
    """Render an Article as a standards-compatible RSS item."""

    def __init__(self, *, feed_url: str = "") -> None:
        self.feed_url = feed_url

    @property
    def name(self) -> str:
        return "rss"

    def publish(self, article: Article) -> PublishResult:
        item = Element("item")
        SubElement(item, "title").text = article.title
        SubElement(item, "link").text = article.url
        SubElement(item, "guid", isPermaLink="true").text = article.url
        SubElement(item, "description").text = article.content
        SubElement(item, "pubDate").text = format_datetime(article.published_at)
        if article.category:
            SubElement(item, "category").text = article.category
        return PublishResult(True, self.name, external_id=article.url)

    def render(self, article: Article) -> str:
        return tostring(self._item(article), encoding="unicode")

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
