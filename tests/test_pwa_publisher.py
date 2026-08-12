import json
from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.publishing.pwa import PWAPublisher


def test_pwa_render_is_valid_json_and_preserves_article_fields():
    article = Article(
        id="1",
        title="خبر تست",
        url="https://example.com/1",
        content="محتوای خبر",
        source="test",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        category="technology",
    )
    payload = json.loads(PWAPublisher().render(article))
    assert payload["id"] == "1"
    assert payload["title"] == "خبر تست"
    assert payload["tags"] == ["technology"]
    assert payload["date_published"].startswith("2026-01-01")


def test_pwa_publish_returns_delivery_result():
    article = Article(
        id="1",
        title="خبر",
        url="https://example.com/1",
        content="محتوا",
        source="test",
        published_at=datetime.now(UTC),
    )
    result = PWAPublisher().publish(article)
    assert result.success
    assert result.destination == "pwa"
    assert result.external_id == "1"
