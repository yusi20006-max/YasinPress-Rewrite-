from __future__ import annotations

import re
from html import escape
from urllib.parse import urlparse

import httpx

from yasinpress.database.models import Article
from yasinpress.processing.breaking import detect_breaking
from yasinpress.publishing import Publisher, PublishResult

# Unicode bidirectional controls for stable Persian layout in chat clients.
_RLM = "\u200f"
_RLE = "\u202b"
_PDF = "\u202c"
_LRI = "\u2066"
_PDI = "\u2069"
_LTR_RUN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/+%-]*")


def _isolate_ltr_runs(text: str) -> str:
    """Wrap Latin/ASCII runs so they stay LTR inside Persian text."""
    return _LTR_RUN.sub(lambda match: f"{_LRI}{match.group(0)}{_PDI}", text)


def _rtl(text: str) -> str:
    """Force a segment to render right-to-left in HTML chat clients."""
    return f"{_RLE}{_RLM}{_isolate_ltr_runs(text)}{_PDF}"


def _rtl_bold(text: str) -> str:
    """Render a bold segment inside an explicit RTL embedding."""
    return f"{_RLE}{_RLM}<b>{_isolate_ltr_runs(text)}</b>{_PDF}"


class EitaaPublisher(Publisher):
    """Publish formatted articles through the Eitaa Yar Bot API."""

    def __init__(self, *, token: str, channel: str, api_base: str = "https://eitaayar.ir/api", timeout: float = 20.0) -> None:
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
        """Render the canonical Eitaa message with deterministic RTL layout."""
        import os
        from datetime import UTC, datetime

        from yasinpress.core.helpers import format_persian_datetime

        source = escape(self._source_label(article))
        breaking = detect_breaking(article.title, article.content, published_at=article.published_at).is_breaking

        lines: list[str] = []
        if breaking:
            lines.extend([_rtl_bold("خبر فوری"), ""])

        lines.extend([_rtl_bold(escape(article.title)), "", _rtl(escape(article.content))])

        if article.ai_modified:
            lines.extend(["", _rtl("<i>بازنویسی‌شده با هوش مصنوعی</i>")])

        timezone_str = os.getenv("YASINPRESS_TIMEZONE", "Asia/Tehran")
        if article.updated_at is not None and article.updated_at != datetime.fromtimestamp(0, tz=UTC):
            time_str = f"زمان به‌روزرسانی: {format_persian_datetime(article.updated_at, timezone_str)}"
        elif article.published_at is not None and article.published_at != datetime.fromtimestamp(0, tz=UTC):
            time_str = f"زمان خبر: {format_persian_datetime(article.published_at, timezone_str)}"
        else:
            time_str = "زمان انتشار: نامشخص"

        lines.extend(["", _rtl(time_str), _rtl(f"منبع: {source}")])
        return f"{_RLE}{_RLM}" + "\n".join(lines) + f"{_PDF}"

    def publish(self, article: Article) -> PublishResult:
        url = f"{self.api_base}/{self.token}/sendMessage"
        payload = {"chat_id": self.channel, "text": self.render(article), "parse_mode": "HTML", "disable_web_page_preview": "true"}
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
            return PublishResult(False, self.name, error=f"Eitaa API rejected request: {error or 'unknown error'}")
        result = data.get("result")
        external_id = str(result["message_id"]) if isinstance(result, dict) and result.get("message_id") is not None else None
        return PublishResult(True, self.name, external_id=external_id or self.channel)
