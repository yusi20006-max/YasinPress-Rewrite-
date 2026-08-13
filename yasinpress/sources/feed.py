"""RSS feed parsing."""

import email.utils
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class FeedItem:
    """An item parsed from an RSS feed."""

    title: str
    url: str
    content: str
    published_at: datetime
    source: str = ""
    media_url: str | None = None
    media_type: str | None = None


def _published_at(item: ET.Element) -> datetime:
    """Return the RSS publication time, or the Unix epoch when unavailable."""
    raw = (item.findtext("pubDate") or item.findtext("published") or "").strip()
    if raw:
        try:
            parsed = email.utils.parsedate_to_datetime(raw)
            return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except (TypeError, ValueError, IndexError):
            pass
    return datetime.fromtimestamp(0, tz=UTC)


def parse_rss(xml_text: str) -> list[FeedItem]:
    """Parse RSS XML using the standard library."""
    root = ET.fromstring(xml_text)
    items: list[FeedItem] = []

    namespaces = {"media": "http://search.yahoo.com/mrss/", "atom": "http://www.w3.org/2005/Atom"}

    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        url = item.findtext("link", "").strip()
        content = (
            item.findtext("description")
            or item.findtext("{http://www.w3.org/2005/Atom}summary")
            or ""
        ).strip()

        enclosure = item.find("enclosure")
        media_url = None
        media_type = None
        if enclosure is not None:
            media_url = enclosure.get("url")
            media_type = enclosure.get("type")

        if not media_url:
            media_content = item.find("media:content", namespaces) or item.find(
                ".//{http://search.yahoo.com/mrss/}content"
            )
            if media_content is not None:
                media_url = media_content.get("url")
                media_type = media_content.get("type")

        if title and url:
            items.append(
                FeedItem(
                    title=title,
                    url=url,
                    content=content,
                    published_at=_published_at(item),
                    media_url=media_url,
                    media_type=media_type,
                )
            )
    return items
