from __future__ import annotations

import httpx

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult


class EitaaPublisher(Publisher):
    """Publish text articles through the Eitaa Yar Bot API."""

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

    def render(self, article: Article) -> str:
        return f"{article.title}\n\n{article.content}\n\n{article.url}"

    def publish(self, article: Article) -> PublishResult:
        url = f"{self.api_base}/{self.token}/sendMessage"
        payload = {"chat_id": self.channel, "text": self.render(article)}
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
