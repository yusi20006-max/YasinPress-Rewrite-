from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.publishing.eitaa import EitaaPublisher


def article(*, ai_modified: bool = False) -> Article:
    return Article(
        id="YP-000001",
        title="خبر آزمایشی",
        url="https://example.com/news/1",
        content="متن خبر",
        source="example.com",
        published_at=datetime.now(UTC),
        ai_modified=ai_modified,
    )


def test_render_contains_clickable_source_link():
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article())
    assert 'href="https://example.com/news/1"' in rendered
    assert "example.com" in rendered
    assert "🤖" not in rendered


def test_render_marks_only_ai_modified_articles():
    publisher = EitaaPublisher(token="token", channel="channel")
    assert "🤖" in publisher.render(article(ai_modified=True))
    assert "🤖" not in publisher.render(article(ai_modified=False))
