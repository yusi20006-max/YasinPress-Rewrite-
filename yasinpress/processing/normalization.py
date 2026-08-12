"""Article normalization."""

from datetime import UTC, datetime

from yasinpress.core.helpers import stable_hash
from yasinpress.database.models import Article
from yasinpress.sources.feed import FeedItem


def normalize(item: FeedItem, source: str, event_id: str | None = None) -> Article:
    """Convert a feed item into an article model with a formatted News ID."""
    pub = item.published_at
    if pub is None:
        pub = datetime.now(UTC)
    elif pub.tzinfo is None:
        pub = pub.replace(tzinfo=UTC)

    yymmdd = pub.strftime("%y%m%d")
    h = stable_hash(item.url)[:6].upper()
    news_id = f"YP-{yymmdd}-{h}"

    return Article(
        id=news_id,
        title=item.title.strip(),
        url=item.url,
        content=item.content.strip(),
        source=source,
        published_at=pub,
        event_id=event_id,
        received_at=datetime.now(UTC),
    )
