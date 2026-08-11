from datetime import UTC, datetime

from yasinpress.processing.cleaner import clean_html
from yasinpress.processing.normalization import normalize
from yasinpress.processing.validator import validate_article
from yasinpress.sources.feed import FeedItem


def test_clean_html() -> None:
    assert clean_html("<b>Hello</b>&nbsp; world") == "Hello world"


def test_normalize_and_validate() -> None:
    article = normalize(
        FeedItem("Title", "https://example.com/a", "Body", datetime.now(UTC)), "src"
    )
    validate_article(article)
    assert article.source == "src"
