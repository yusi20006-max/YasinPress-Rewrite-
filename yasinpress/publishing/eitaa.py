from __future__ import annotations

from urllib.parse import urlparse

import httpx

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult


class EitaaPublisher(Publisher):
    """Publish attributed text articles through the Eitaa Yar Bot API."""

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
        if not hostname:
            return "منبع"
        return hostname.removeprefix("www.")

    @staticmethod
    def _escape_html(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def render(self, article: Article) -> str:
        """Render the public Eitaa message.

        Contract (issue #6):
        - No raw article URL is displayed as text.
        - The source name itself is the clickable link to the original article.
        - The source is never repeated as both a plain label and a separate link.
        - AI-rewritten content is visibly marked with an AI marker.
        - Breaking-priority articles get a clear breaking indicator.
        """
        source = self._escape_html(self._source_label(article))
        title = self._escape_html(article.title)
        content = self._escape_html(article.content)
        source_link = f'<a href="{article.url}">{source}</a>'

        header_parts = []
        if article.priority == "breaking":
            header_parts.append("🔴 فوری")
        header_parts.append(title)
        header = "\n".join(header_parts)

        footer_parts = [f"منبع: {source_link}"]
        if article.is_ai_rewritten:
            footer_parts.append("🤖 بازنویسی با هوش مصنوعی")
        footer = " | ".join(footer_parts)

        return f"{header}\n\n{content}\n\n{footer}"

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
        external_id = None
        if isinstance(result, dict) and result.get("message_id") is not None:
            external_id = str(result["message_id"])
        return PublishResult(True, self.name, external_id=external_id or self.channel)
