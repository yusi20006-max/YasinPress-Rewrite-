from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.publishing.rss import RSSPublisher


def test_rss_render_contains_core_fields():
    article = Article(
        id="1",
        title="خبر تست",
        url="https://example.com/1",
        content="محتوای خبر",
        source="test",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        category="technology",
    )
    xml = RSSPublisher().render(article)
    assert "<title>خبر تست</title>" in xml
    assert "https://example.com/1" in xml
    assert "<description>محتوای خبر</description>" in xml
    assert "<category>technology</category>" in xml


def test_rss_publish_returns_delivery_result():
    article = Article(
        id="1",
        title="خبر",
        url="https://example.com/1",
        content="محتوا",
        source="test",
        published_at=datetime.now(UTC),
    )
    result = RSSPublisher().publish(article)
    assert result.success
    assert result.destination == "rss"
    assert result.external_id == article.url
