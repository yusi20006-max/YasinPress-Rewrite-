"""
Regression tests for Eitaa HTML leakage fix.

Root cause: EitaaPublisher previously emitted HTML tags (<b>, <i>) and
set parse_mode=HTML in the API payload.  Eitaa Yar Bot API does NOT
support HTML parse_mode; it uses Markdown-style formatting (*bold*,
_italic_) by default.  The result was that HTML tags appeared as literal
text in the Eitaa channel.

Fix: render() now produces Markdown, and publish() no longer sends
parse_mode.  These tests guarantee the regression cannot reappear.
"""
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from yasinpress.database.models import Article
from yasinpress.publishing.eitaa import EitaaPublisher

# ── helpers ──────────────────────────────────────────────────────────────────

_FRESH = datetime.now(UTC) - timedelta(hours=1)
_FIXED = datetime(2026, 8, 18, 17, 50, tzinfo=UTC)


def _article(
    *,
    title: str = "خبر آزمایشی",
    content: str = "متن خبر",
    ai_modified: bool = False,
    published_at=_FIXED,
) -> Article:
    return Article(
        id="YP-REG-001",
        title=title,
        url="https://example.com/news/1",
        content=content,
        source="example.com",
        published_at=published_at,
        ai_modified=ai_modified,
    )


def _pub() -> EitaaPublisher:
    return EitaaPublisher(token="tok", channel="chan")


# ── HTML leakage: render() must never emit raw HTML tags ────────────────────

def test_no_html_bold_tag_in_normal_article():
    rendered = _pub().render(_article())
    assert "<b>" not in rendered
    assert "</b>" not in rendered


def test_no_html_italic_tag_in_ai_article():
    rendered = _pub().render(_article(ai_modified=True))
    assert "<i>" not in rendered
    assert "</i>" not in rendered


def test_no_html_tags_in_breaking_article():
    rendered = _pub().render(_article(title="فوری: زلزله شدید در تهران", published_at=_FRESH))
    assert "<b>" not in rendered
    assert "</b>" not in rendered
    assert "<i>" not in rendered
    assert "</i>" not in rendered


def test_no_html_tags_when_title_contains_html():
    rendered = _pub().render(_article(title="<b>عنوان فوری</b>"))
    assert "<b>" not in rendered
    assert "</b>" not in rendered


def test_no_html_tags_when_content_contains_html():
    rendered = _pub().render(_article(content="<b>متن پررنگ</b> و <i>ایتالیک</i>"))
    assert "<b>" not in rendered
    assert "</b>" not in rendered
    assert "<i>" not in rendered
    assert "</i>" not in rendered


# ── Markdown formatting is actually present ───────────────────────────────────

def test_title_wrapped_in_markdown_bold():
    rendered = _pub().render(_article(title="خبر ساده"))
    assert "*خبر ساده*" in rendered


def test_breaking_marker_uses_markdown_bold():
    rendered = _pub().render(_article(title="فوری: زلزله شدید", published_at=_FRESH))
    assert rendered.startswith("*خبر فوری* 🚨\n\n")


def test_ai_marker_uses_markdown_italic():
    rendered = _pub().render(_article(ai_modified=True))
    assert "_بازنویسی‌شده با هوش مصنوعی_ 🤖" in rendered


def test_ai_marker_absent_when_not_ai_modified():
    rendered = _pub().render(_article(ai_modified=False))
    assert "🤖" not in rendered
    assert "_بازنویسی‌شده با هوش مصنوعی_" not in rendered


# ── Persian timestamp preserved ───────────────────────────────────────────────

def test_persian_timestamp_present_in_render(monkeypatch):
    monkeypatch.setenv("YASINPRESS_TIMEZONE", "Asia/Tehran")
    rendered = _pub().render(_article(published_at=datetime(2026, 8, 18, 17, 50, tzinfo=UTC)))
    assert "زمان خبر:" in rendered
    assert "🕐" in rendered
    # Persian digits in timestamp
    assert "۱۴۰۵" in rendered


# ── Realistic Eitaa HTTP payload ──────────────────────────────────────────────

def test_realistic_eitaa_payload_structure():
    """Verify the exact fields sent over HTTP to Eitaa."""
    captured: dict = {}

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"ok": True, "result": {"message_id": 77}}

    with patch("yasinpress.publishing.eitaa.httpx.post", return_value=response) as post:
        result = EitaaPublisher(token="MY-TOKEN", channel="MY-CHANNEL").publish(
            _article(title="عنوان تست واقعی")
        )
        call_kwargs = post.call_args

    assert result.success
    data = call_kwargs.kwargs["data"]

    # Required fields
    assert data["chat_id"] == "MY-CHANNEL"
    assert "text" in data

    # parse_mode must NOT be present (Eitaa ignores/breaks on HTML mode)
    assert "parse_mode" not in data, (
        "parse_mode must not be sent; Eitaa renders HTML tags as literal text"
    )

    # HTML must not appear in the text field
    text = data["text"]
    assert "<b>" not in text, f"<b> leaked into payload: {text!r}"
    assert "</b>" not in text, f"</b> leaked into payload: {text!r}"
    assert "<i>" not in text, f"<i> leaked into payload: {text!r}"
    assert "</i>" not in text, f"</i> leaked into payload: {text!r}"

    # Title in Markdown bold
    assert "*عنوان تست واقعی*" in text

    # Source and timestamp
    assert "منبع:" in text
    assert "🕐" in text


def test_payload_for_breaking_article():
    """Breaking article payload must use Markdown, not HTML."""
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"ok": True, "result": {"message_id": 1}}

    with patch("yasinpress.publishing.eitaa.httpx.post", return_value=response) as post:
        EitaaPublisher(token="t", channel="c").publish(
            _article(title="فوری: زلزله شدید", published_at=_FRESH)
        )
        text = post.call_args.kwargs["data"]["text"]

    assert text.startswith("*خبر فوری* 🚨\n\n")
    assert "<b>" not in text
    assert "</b>" not in text


def test_payload_for_ai_modified_article():
    """AI-modified article payload must use Markdown italic."""
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"ok": True, "result": {"message_id": 2}}

    with patch("yasinpress.publishing.eitaa.httpx.post", return_value=response) as post:
        EitaaPublisher(token="t", channel="c").publish(_article(ai_modified=True))
        text = post.call_args.kwargs["data"]["text"]

    assert "_بازنویسی‌شده با هوش مصنوعی_ 🤖" in text
    assert "<i>" not in text
    assert "</i>" not in text
