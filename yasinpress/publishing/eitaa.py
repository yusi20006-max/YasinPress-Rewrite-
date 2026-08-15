from __future__ import annotations

import os
from datetime import UTC, datetime
from html import escape
from urllib.parse import urlparse

import httpx

from yasinpress.database.models import Article
from yasinpress.processing.breaking import detect_breaking
from yasinpress.publishing import Publisher, PublishResult


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

        Directionality is deliberately left to the Eitaa client. Injecting
        Unicode bidi controls into the serialized HTML corrupts HTML entities,
        makes exact output non-deterministic, and breaks downstream consumers.
        """
        from yasinpress.core.helpers import format_persian_datetime

        source = escape(self._source_label(article))
        breaking = detect_breaking(
            article.title,
            article.content,
            published_at=article.published_at,
        ).is_breaking

        lines: list[str] = []
        if breaking:
            lines.extend(["🚨 <b>خبر فوری</b>", ""])

        lines.extend([
            f"<b>{escape(article.title)}</b>",
            "",
            escape(article.content),
        ])

        if article.ai_modified:
            lines.extend(["", "🤖 <i>بازنویسی‌شده با هوش مصنوعی</i>"])

        timezone_str = os.getenv("YASINPRESS_TIMEZONE", "Asia/Tehran")
        epoch = datetime.fromtimestamp(0, tz=UTC)
        if article.updated_at is not None and article.updated_at != epoch:
            time_str = (
                "🕐 آخرین به‌روزرسانی: "
                f"{format_persian_datetime(article.updated_at, timezone_str)}"
            )
        elif article.published_at is not None and article.published_at != epoch:
            time_str = f"🕐 زمان خبر: {format_persian_datetime(article.published_at, timezone_str)}"
        else:
            time_str = "🕐 زمان انتشار: نامشخص"

        lines.extend(["", time_str, f"منبع: {source}"])
        return "\n".join(lines)

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
