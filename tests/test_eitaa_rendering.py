from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.publishing.eitaa import EitaaPublisher, _clean_title

_BIDI = (
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u200e",
    "\u200f",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
)
_ESC_LT = chr(38) + "lt;"
_ESC_GT = chr(38) + "gt;"


def article(*, ai_modified: bool = False, title: str = "عنوان آزمایشی") -> Article:
    return Article(
        id="YSN-000001",
        title=title,
        url="https://example.com/news/1",
        content="متن خبر",
        source="Example",
        published_at=datetime(2026, 8, 18, 17, 50, tzinfo=UTC),
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
    rendered = publisher().render(article(title="فوری: زلزله شدید در تهران"))
    assert rendered.startswith("<b>خبر فوری</b> 🚨\n\n")
    assert "<b>فوری: زلزله شدید در تهران</b>" in rendered


def test_normal_article_has_no_breaking_marker():
    rendered = publisher().render(article())
    assert "🚨" not in rendered
    assert "خبر فوری" not in rendered


def test_raw_url_is_not_rendered_as_plain_text():
    rendered = publisher().render(article())
    assert "منبع: https://example.com/news/1" not in rendered
    assert "منبع: example.com" in rendered


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
    assert _ESC_LT + "script" + _ESC_GT in rendered


def test_no_invisible_bidi_controls_in_serialized_html():
    rendered = publisher().render(article(ai_modified=True, title="فوری: تست"))
    for ch in _BIDI:
        assert ch not in rendered


def test_marker_blocks_are_not_emoji_led():
    """Logical blocks must not start with neutral emoji."""
    rendered = publisher().render(article(ai_modified=True, title="فوری: زلزله شدید"))
    for line in rendered.splitlines():
        stripped = line.lstrip()
        if not stripped:
            continue
        if stripped[0] in "🚨🤖🕐":
            raise AssertionError(f"emoji-led block: {stripped!r}")


def test_reported_persian_titles_are_normalized_before_eitaa_html():
    titles = [
        "نشست تخصصی اصحاب رسانه درباره جنگ شناختی",
        "رژیم صهیونیستی مدعی حمله به جلسه رهبران مقاومت در غزه",
        "حمله توپخانه ای رژیم صهیونیستی به جنوب سوریه",
    ]
    for title in titles:
        rendered = publisher().render(article(title=title))
        assert rendered.startswith(f"<b>{title}</b>\n\n")
        assert title in rendered


def test_title_metadata_and_punctuation_noise_are_removed_without_destroying_meaning():
    title = "حمله توپخانه ای رژیم صهیونیستی به جنوب سوریه - خبرگزاری ایرنا"
    assert _clean_title(title) == "حمله توپخانه ای رژیم صهیونیستی به جنوب سوریه"

    quoted = "پایان رزمایش؛ «گزارش نهایی» - خبرگزاری مهر"
    assert _clean_title(quoted) == "پایان رزمایش؛ «گزارش نهایی»"


def test_exact_canonical_normal_message_layout():
    title = "نشست تخصصی اصحاب رسانه درباره جنگ شناختی"
    rendered = publisher().render(article(title=title))
    assert rendered == (
        "<b>نشست تخصصی اصحاب رسانه درباره جنگ شناختی</b>\n\n"
        "متن خبر\n\n"
        "زمان خبر: ۲۷ مرداد ۱۴۰۵، ۲۱:۲۰ 🕐\n"
        "منبع: example.com"
    )


def test_exact_canonical_breaking_message_layout():
    rendered = publisher().render(article(title="فوری: زلزله شدید در تهران"))
    assert rendered == (
        "<b>خبر فوری</b> 🚨\n\n"
        "<b>فوری: زلزله شدید در تهران</b>\n\n"
        "متن خبر\n\n"
        "زمان خبر: ۲۷ مرداد ۱۴۰۵، ۲۱:۲۰ 🕐\n"
        "منبع: example.com"
    )
