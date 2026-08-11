"""Article normalization."""

from yasinpress.core.helpers import stable_hash
from yasinpress.database.models import Article
from yasinpress.sources.feed import FeedItem


def normalize(item: FeedItem, source: str) -> Article:
    """Convert a feed item into an article model."""
    return Article(
        id=stable_hash(item.url),
        title=item.title.strip(),
        url=item.url,
        content=item.content.strip(),
        source=source,
        published_at=item.published_at,
    )
