from datetime import UTC, datetime, timedelta

from yasinpress.database.models import Article
from yasinpress.publishing.eitaa import EitaaPublisher, _clean_title

_BIDI = (
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
    "\u200e", "\u200f", "\u2066", "\u2067", "\u2068", "\u2069",
)


def article(*, ai_modified: bool = False, title: str = "عنوان آزمایشی", published_at=None) -> Article:
    return Article(
        id="YSN-000001",
        title=title,
        url="https://example.com/news/1",
        content="متن خبر",
        source="Example",
        published_at=published_at or datetime(2026, 8, 18, 17, 50, tzinfo=UTC),
        ai_modified=ai_modified,
    )


def publisher() -> EitaaPublisher:
    return EitaaPublisher(token="test-token", channel="test-channel")


def test_source_is_plain_domain_without_html_link():
    rendered = publisher().render(article())
    assert rendered.endswith("منبع: example.com")
    assert "<a " not in rendered
    assert "href=" not in rendered
    assert "https://example.com/news/1" not in rendered


def test_ai_marker_only_when_article_was_modified():
    assert "🤖" not in publisher().render(article(ai_modified=False))
    assert "🤖" in publisher().render(article(ai_modified=True))


def test_breaking_marker_is_emitted_for_fresh_severe_news():
    # Eitaa uses Markdown (*bold*), not HTML (<b>)
    fresh = datetime.now(UTC) - timedelta(hours=1)
    rendered = publisher().render(article(title="فوری: زلزله شدید در تهران", published_at=fresh))
    assert rendered.startswith("*خبر فوری* 🚨\n\n")
    assert "*فوری: زلزله شدید در تهران*" in rendered
    # HTML tags must NEVER appear in output
    assert "<b>" not in rendered
    assert "</b>" not in rendered


def test_normal_article_has_no_breaking_marker():
    rendered = publisher().render(article())
    assert "🚨" not in rendered
    assert "خبر فوری" not in rendered


def test_raw_url_is_not_rendered_as_plain_text():
    rendered = publisher().render(article())
    assert "منبع: https://example.com/news/1" not in rendered
    assert "منبع: example.com" in rendered


def test_html_tags_never_leaked_to_output():
    """Core regression: no HTML tag must survive into the Eitaa payload."""
    item = Article(
        id="YSN-000001",
        title='<script>alert("x")</script>',
        url="https://example.com/news/1",
        content="<b>unsafe</b>",
        source="Example",
        published_at=datetime(2026, 8, 18, 17, 50, tzinfo=UTC),
    )
    rendered = publisher().render(item)
    # script tags stripped
    assert "<script>" not in rendered
    assert "</script>" not in rendered
    # HTML bold tags must NOT appear
    assert "<b>" not in rendered
    assert "</b>" not in rendered
    # the alert text should still be visible (stripped of tags)
    assert "alert" in rendered
    # content plain text appears
    assert "unsafe" in rendered


def test_no_invisible_bidi_controls_in_rendered_output():
    rendered = publisher().render(article(ai_modified=True, title="فوری: تست"))
    for ch in _BIDI:
        assert ch not in rendered


def test_marker_blocks_are_not_emoji_led():
    """Logical blocks must not start with neutral emoji."""
    rendered = publisher().render(article(ai_modified=True, title="فوری: زلزله شدید"))
    for line in rendered.splitlines():
        stripped = line.lstrip()
        if stripped and stripped[0] in "🚨🤖🕐":
            raise AssertionError(f"emoji-led block: {stripped!r}")


def test_reported_persian_titles_are_normalized_before_eitaa_markdown():
    # Eitaa uses Markdown bold (*title*), not HTML bold (<b>title</b>)
    titles = [
        "نشست تخصصی اصحاب رسانه درباره جنگ شناختی",
        "رژیم صهیونیستی مدعی حمله به جلسه رهبران مقاومت در غزه",
        "حمله توپخانه ای رژیم صهیونیستی به جنوب سوریه",
    ]
    for title in titles:
        rendered = publisher().render(article(title=title))
        assert f"*{title}*" in rendered
        assert rendered.count(f"*{title}*") == 1
        assert "خبرگزاری" not in _clean_title(title)
        # Absolutely no HTML bold tags
        assert "<b>" not in rendered
        assert "</b>" not in rendered


def test_title_metadata_and_punctuation_noise_are_removed_without_destroying_meaning():
    title = "حمله توپخانه ای رژیم صهیونیستی به جنوب سوریه - خبرگزاری ایرنا"
    assert _clean_title(title) == "حمله توپخانه ای رژیم صهیونیستی به جنوب سوریه"
    quoted = "پایان رزمایش؛ «گزارش نهایی» - خبرگزاری مهر"
    assert _clean_title(quoted) == "پایان رزمایش؛ «گزارش نهایی»"


def test_exact_canonical_normal_message_layout():
    # Eitaa Markdown format: *bold* instead of <b>bold</b>
    title = "نشست تخصصی اصحاب رسانه درباره نشست تخصصی"
    rendered = publisher().render(article(title=title))
    assert rendered == (
        "*نشست تخصصی اصحاب رسانه درباره نشست تخصصی*\n\n"
        "متن خبر\n\n"
        "زمان خبر: ۲۷ مرداد ۱۴۰۵، ۲۱:۲۰ 🕐\n"
        "منبع: example.com"
    )


def test_exact_canonical_breaking_message_layout():
    # Eitaa Markdown: *خبر فوری* instead of <b>خبر فوری</b>
    fresh = datetime.now(UTC) - timedelta(hours=1)
    rendered = publisher().render(article(title="فوری: زلزله شدید در تهران", published_at=fresh))
    assert rendered.startswith(
        "*خبر فوری* 🚨\n\n*فوری: زلزله شدید در تهران*\n\n"
    )
    assert rendered.endswith("منبع: example.com")
