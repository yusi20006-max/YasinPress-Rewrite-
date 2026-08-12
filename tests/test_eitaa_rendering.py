from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.publishing.eitaa import EitaaPublisher


def article(*, ai_modified: bool = False) -> Article:
    return Article(
        id="YSN-000001",
        title="عنوان آزمایشی",
        url="https://example.com/news/1",
        content="متن خبر",
        source="Example",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        ai_modified=ai_modified,
    )


def publisher() -> EitaaPublisher:
    return EitaaPublisher(token="test-token", channel="test-channel")


def test_source_is_clickable_html_link():
    rendered = publisher().render(article())
    assert 'href="https://example.com/news/1"' in rendered
    assert ">example.com</a>" in rendered
    assert "<a " in rendered


def test_ai_marker_only_when_article_was_modified():
    assert "🤖" not in publisher().render(article(ai_modified=False))
    assert "🤖" in publisher().render(article(ai_modified=True))


def test_html_is_escaped():
    item = article()
    item = Article(
        id=item.id,
        title='<script>alert("x")</script>',
        url=item.url,
        content="<b>unsafe</b>",
        source=item.source,
        published_at=item.published_at,
    )
    rendered = publisher().render(item)
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
