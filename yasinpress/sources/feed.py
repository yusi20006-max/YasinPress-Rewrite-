"""RSS feed parsing."""

import email.utils
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class FeedItem:
    """An item parsed from an RSS feed."""

    title: str
    url: str
    content: str
    published_at: datetime | None = None
    source: str = ""
    media_url: str | None = None
    media_type: str | None = None
    updated_at: datetime | None = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def _parse_date(raw: str | None) -> datetime | None:
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except (TypeError, ValueError, IndexError):
        pass
    try:
        # ISO 8601 parsing
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except (TypeError, ValueError, IndexError):
        pass
    return None


def _published_at(item: ET.Element) -> datetime:
    """Return the feed publication time, or epoch when unavailable/invalid."""
    is_atom = item.tag == "{http://www.w3.org/2005/Atom}entry"
    if is_atom:
        raw = item.findtext("{http://www.w3.org/2005/Atom}published") or item.findtext("{http://www.w3.org/2005/Atom}updated")
    else:
        raw = item.findtext("pubDate") or item.findtext("published") or item.findtext("updated")

    parsed = _parse_date(raw)
    return parsed if parsed else datetime.fromtimestamp(0, tz=UTC)


def parse_rss(xml_text: str) -> list[FeedItem]:
    """Parse RSS or Atom XML using the standard library."""
    root = ET.fromstring(xml_text)
    items: list[FeedItem] = []

    namespaces = {"media": "http://search.yahoo.com/mrss/"}
    rss_items = root.findall(".//item")
    atom_entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    for item in [*rss_items, *atom_entries]:
        is_atom = item.tag == "{http://www.w3.org/2005/Atom}entry"
        if is_atom:
            title = item.findtext("{http://www.w3.org/2005/Atom}title", "")
            link_element = item.find("{http://www.w3.org/2005/Atom}link")
            url = link_element.get("href", "") if link_element is not None else ""
            content = (
                item.findtext("{http://www.w3.org/2005/Atom}content")
                or item.findtext("{http://www.w3.org/2005/Atom}summary")
                or ""
            )
            pub_val = item.findtext("{http://www.w3.org/2005/Atom}published")
            upd_val = item.findtext("{http://www.w3.org/2005/Atom}updated")
        else:
            title = item.findtext("title", "")
            url = item.findtext("link", "")
            content = item.findtext("description") or ""
            pub_val = item.findtext("pubDate") or item.findtext("published")
            upd_val = item.findtext("updated")

        title = title.strip()
        url = url.strip()
        content = content.strip()

        published_at = _parse_date(pub_val)
        updated_at = _parse_date(upd_val)

        # If published is missing but updated is present, fallback
        if published_at is None and updated_at is not None:
            published_at = updated_at

        # Backward compatibility fallback to epoch when unavailable
        if published_at is None:
            published_at = datetime.fromtimestamp(0, tz=UTC)

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
                    published_at=published_at,
                    updated_at=updated_at,
                    source="",
                    media_url=media_url,
                    media_type=media_type,
                )
            )
    return items
