from datetime import UTC, datetime, timedelta

from yasinpress.database.models import Article
from yasinpress.publishing.eitaa import EitaaPublisher


def article(*, ai_modified: bool = False, title: str = "خبر آزمایشی", content: str = "متن خبر") -> Article:
    return Article(
        id="YP-000001",
        title=title,
        url="https://example.com/news/1",
        content=content,
        source="example.com",
        published_at=datetime.now(UTC) - timedelta(minutes=10),
        ai_modified=ai_modified,
    )


def test_render_uses_plain_source_label_without_url_or_link_markup():
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article())
    assert "<b>خبر آزمایشی</b>" in rendered
    assert "متن خبر" in rendered
    assert "منبع: example.com" in rendered
    assert "🕐" in rendered
    assert "https://" not in rendered
    assert "<a " not in rendered
    assert "🤖" not in rendered


def test_render_marks_only_ai_modified_articles():
    publisher = EitaaPublisher(token="token", channel="channel")
    assert "🤖 <b>خبر آزمایشی</b>" in publisher.render(article(ai_modified=True))
    assert "🤖" not in publisher.render(article(ai_modified=False))


def test_render_uses_breaking_header_for_fresh_severe_news():
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article(title="فوری: زلزله شدید"))
    assert rendered.startswith("🚨 <b>خبر فوری</b>\n\n")
    assert "<b>فوری: زلزله شدید</b>" in rendered
    assert "منبع: example.com" in rendered
    assert "https://" not in rendered
    assert "<a " not in rendered


def test_render_escapes_article_content():
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article(title="A < B", content="x > y & z"))
    assert "<b>A &lt; B</b>" in rendered
    assert "x &gt; y &amp; z" in rendered
