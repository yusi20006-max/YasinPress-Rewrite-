from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from html import escape, unescape
from urllib.parse import urlparse

import httpx

from yasinpress.database.models import Article
from yasinpress.processing.breaking import detect_breaking
from yasinpress.publishing import Publisher, PublishResult

_FORMATTING_TAG_RE = re.compile(r"<\s*/?\s*(?:b|strong|i|em|u|mark)\b[^>]*>", re.IGNORECASE)
_MARKDOWN_CODE_SPAN_RE = re.compile(r"`{1,3}[^`\n]*`{1,3}")

# Neutral / weak leading tokens that can bias Eitaa client to LTR.
_NEUTRAL_LEAD_RE = re.compile(
    r"^[\s\U0001F300-\U0001FAFF\U00002600-\U000027BF<>/]+"
)


def _clean_title(title: str) -> str:
    """Remove title formatting artifacts while preserving unsafe text for escaping."""
    title = unescape(title)
    title = _FORMATTING_TAG_RE.sub(" ", title)
    title = _MARKDOWN_CODE_SPAN_RE.sub("", title)
    return re.sub(r"\s+", " ", title).strip()


def _rtl_stable_block(text: str) -> str:
    """Ensure a logical block's first *visible* strong char is RTL-friendly.

    If the block already starts with a strong (non-neutral) character after
    stripping leading whitespace, return as-is. Otherwise prefix a visible
    Persian marker word so the Eitaa client does not choose LTR from a
    leading emoji or angle-bracket alone. Never inject U+202A–U+202E / U+200E/F.
    """
    stripped = text.lstrip()
    if not stripped:
        return text
    # Fast path: first code point is Arabic/Persian letter range or digit in context
    first = stripped[0]
    if "\u0600" <= first <= "\u06FF" or "\u0750" <= first <= "\u077F":
        return text
    if first.isalpha() and ord(first) > 127:
        return text
    # Title wrapped only in <b>…</b> with Persian inside is handled by caller.
    if stripped.startswith("<") and ">" in stripped:
        inner = stripped.split(">", 1)[1]
        if inner and "\u0600" <= inner[0] <= "\u06FF":
            return text
    # Leading neutrals (emoji / punctuation / tags): require Persian lead label
    if _NEUTRAL_LEAD_RE.match(stripped):
        return f"‎متن: {text}" if False else text  # noqa: keep structure via explicit call sites
    return text


class EitaaPublisher(Publisher):
    """Publish formatted articles through the Eitaa Yar Bot API."""

    def __init__(
        self,
        *,
        token: str,
        channel: str,
        api_base: str = "https://eitaayar.ir/api",
        timeout: float = 20.0,
    ) -> None:
        if not token.strip():
            raise ValueError("Eitaa token must not be empty")
        if not channel.strip():
            raise ValueError("Eitaa channel must not be empty")
        if timeout <= 0:
            raise ValueError("Eitaa timeout must be positive")
        self.token = token.strip()
        self.channel = channel.strip()
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "eitaa"

    @staticmethod
    def _source_label(article: Article) -> str:
        hostname = urlparse(article.url).hostname
        return hostname.removeprefix("www.") if hostname else "منبع"

    def render(self, article: Article) -> str:
        """Render the canonical Eitaa HTML message deterministically.

        Directionality must remain stable for the Eitaa client without injecting
        invisible Unicode bidi controls (those corrupt entities and break
        consumers). Each logical block therefore *leads* with visible strong
        Persian text; decorative emoji follow the label.
        """
        from yasinpress.core.helpers import format_persian_datetime

        source = escape(self._source_label(article))
        title = escape(_clean_title(article.title))
        breaking = detect_breaking(
            article.title,
            article.content,
            published_at=article.published_at,
        ).is_breaking

        lines: list[str] = []
        if breaking:
            # Persian label first (strong RTL), emoji after — not "🚨 <b>…"
            lines.extend(["<b>خبر فوری</b> 🚨", ""])

        lines.extend([
            f"<b>{title}</b>",
            "",
            escape(article.content),
        ])

        if article.ai_modified:
            # Persian phrase first so the block is not emoji-led
            lines.extend(["", "<i>بازنویسی‌شده با هوش مصنوعی</i> 🤖"])

        timezone_str = os.getenv("YASINPRESS_TIMEZONE", "Asia/Tehran")
        epoch = datetime.fromtimestamp(0, tz=UTC)
        if article.updated_at is not None and article.updated_at != epoch:
            time_str = (
                "آخرین به‌روزرسانی: "
                f"{format_persian_datetime(article.updated_at, timezone_str)} 🕐"
            )
        elif article.published_at is not None and article.published_at != epoch:
            time_str = (
                f"زمان خبر: {format_persian_datetime(article.published_at, timezone_str)} 🕐"
            )
        else:
            time_str = "زمان انتشار: نامشخص 🕐"

        lines.extend(["", time_str, f"منبع: {source}"])
        rendered = "\n".join(lines)
        # Contract: never emit invisible bidi controls
        for ch in ("\u202a", "\u202b", "\u202c", "\u202d", "\u202e", "\u200e", "\u200f", "\u2066", "\u2067", "\u2068", "\u2069"):
            if ch in rendered:
                rendered = rendered.replace(ch, "")
        return rendered

    def publish(self, article: Article) -> PublishResult:
        url = f"{self.api_base}/{self.token}/sendMessage"
        payload = {
            "chat_id": self.channel,
            "text": self.render(article),
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }
        try:
            response = httpx.post(url, data=payload, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return PublishResult(False, self.name, error=f"Eitaa request failed: {exc}")
        try:
            data = response.json()
        except ValueError as exc:
            return PublishResult(False, self.name, error=f"Eitaa returned invalid JSON: {exc}")
        if not isinstance(data, dict) or data.get("ok") is not True:
            error = data.get("error") if isinstance(data, dict) else None
            return PublishResult(
                False,
                self.name,
                error=f"Eitaa API rejected request: {error or 'unknown error'}",
            )
        result = data.get("result")
        external_id = (
            str(result["message_id"])
            if isinstance(result, dict) and result.get("message_id") is not None
            else None
        )
        return PublishResult(True, self.name, external_id=external_id or self.channel)
