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
    # Eitaa uses Markdown (*bold*), NOT HTML (<b>)
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article(title="فوری: زلزله شدید"))
    assert rendered.startswith("*خبر فوری* 🚨\n\n")
    assert "*فوری: زلزله شدید*" in rendered
    assert "منبع: example.com" in rendered
    assert "https://" not in rendered
    assert "<a " not in rendered
    # HTML leakage regression guard
    assert "<b>" not in rendered
    assert "</b>" not in rendered


def test_no_html_tags_in_any_rendered_output():
    """Regression: HTML tags must never appear in Eitaa payload text."""
    publisher = EitaaPublisher(token="token", channel="channel")
    for a in [
        article(),
        article(ai_modified=True),
        article(title="فوری: زلزله شدید"),
        article(title="<b>خبر فوری</b> `CODE`"),
        article(content="<b>unsafe</b> & <i>italic</i>"),
    ]:
        rendered = publisher.render(a)
        assert "<b>" not in rendered, f"<b> leaked: {rendered!r}"
        assert "</b>" not in rendered, f"</b> leaked: {rendered!r}"
        assert "<i>" not in rendered, f"<i> leaked: {rendered!r}"
        assert "</i>" not in rendered, f"</i> leaked: {rendered!r}"


def test_render_strips_html_from_content():
    # Content HTML must be stripped, not passed through
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article(content="x > y & z"))
    # Angle-bracket entities should not appear (no HTML escaping of plain text)
    assert "&gt;" not in rendered
    assert "&amp;" not in rendered
    # The plain values should appear directly
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
    # No double-bold wrapping
    assert "**" not in rendered.replace("\\*", "")
    assert "CODE" not in rendered


def test_time_and_ai_blocks_are_persian_led():
    publisher = EitaaPublisher(token="token", channel="channel")
    rendered = publisher.render(article(ai_modified=True))
    assert "زمان خبر:" in rendered
    assert "🕐" in rendered
    assert not any(
        line.lstrip().startswith("🕐") for line in rendered.splitlines() if line.strip()
    )
    # AI marker uses Markdown italic (_text_), not HTML <i>
    assert "_بازنویسی‌شده با هوش مصنوعی_ 🤖" in rendered
    assert "<i>" not in rendered
    assert "</i>" not in rendered
