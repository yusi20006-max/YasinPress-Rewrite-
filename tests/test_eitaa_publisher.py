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
    assert "خبر آزمایشی" in rendered
    assert "متن خبر" in rendered
    assert "منبع: example.com" in rendered
    assert "زمان خبر:" in rendered
    assert "https://" not in rendered
    assert "<a " not in rendered
    assert "🚨" not in rendered
    assert "🤖" not in rendered
    assert "\u202b" not in rendered
    assert "\u202c" not in rendered
    assert "\u200f" not in rendered


def test_render_marks_only_ai_modified_articles():
    publisher = EitaaPublisher(token="token", channel="channel")
    assert "🤖" in publisher.render(article(ai_modified=True))
    assert "بازنویسی‌شده با هوش مصنوعی" in publisher.render(article(ai_modified=True))
    assert "🤖" not in publisher.render(article(ai_modified=False))
    assert "بازنویسی‌شده با هوش مصنوعی" not in publisher.render(article(ai_modified=False))


def test_render_uses_breaking_header_for_fresh_severe_news():
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article(title="فوری: زلزله شدید"))
    assert rendered.startswith("<b>خبر فوری</b> 🚨\n\n")
    assert "<b>فوری: زلزله شدید</b>" in rendered
    assert "منبع: example.com" in rendered
    assert "https://" not in rendered
    assert "<a " not in rendered


def test_render_escapes_article_content():
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article(title="A < B", content="x > y & z"))
    assert "A < B" in rendered
    assert "x > y & z" in rendered


def test_mixed_script_title_remains_plain_and_deterministic():
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article(title="خبر از BBC و CNN"))
    assert "خبر از BBC و CNN" in rendered
    assert "\u2066" not in rendered
    assert "\u2069" not in rendered


def test_render_removes_title_html_and_markdown_artifacts():
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article(title="<b>خبر فوری</b> `CODE`"))
    assert "خبر فوری" in rendered
    assert "<b><b>" not in rendered
    assert "CODE" not in rendered
    assert "`" not in rendered


def test_time_and_ai_blocks_are_persian_led():
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article(ai_modified=True))
    assert "زمان خبر:" in rendered
    assert "🕐" in rendered
    assert not any(
        line.lstrip().startswith("🕐") for line in rendered.splitlines() if line.strip()
    )
    assert "<i>بازنویسی‌شده با هوش مصنوعی</i> 🤖" in rendered
