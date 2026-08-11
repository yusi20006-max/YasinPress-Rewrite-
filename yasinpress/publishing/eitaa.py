from __future__ import annotations

import httpx

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult


class EitaaPublisher(Publisher):
    """Publish articles through the EitaaYar sendMessage endpoint."""

    def __init__(
        self,
        *,
        channel: str,
        token: str,
        timeout_seconds: float = 20.0,
        base_url: str = "https://eitaayar.ir/api",
        client: httpx.Client | None = None,
    ) -> None:
        if not channel:
            raise ValueError("channel must not be empty")
        if not token:
            raise ValueError("token must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.channel = channel
        self.token = token
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url.rstrip("/")
        self._client = client

    @property
    def name(self) -> str:
        return "eitaa"

    def render(self, article: Article) -> str:
        return f"{article.title}\n\n{article.content}\n\n{article.url}"

    def _request(self, text: str) -> tuple[bool, str | None, str | None]:
        url = f"{self.base_url}/{self.token}/sendMessage"
        data = {"chat_id": self.channel, "text": text}

        try:
            if self._client is not None:
                response = self._client.post(url, data=data, timeout=self.timeout_seconds)
            else:
                response = httpx.post(url, data=data, timeout=self.timeout_seconds)
        except httpx.HTTPError as exc:
            return False, None, f"Eitaa request failed: {exc}"

        try:
            payload = response.json()
        except ValueError:
            payload = {}

        if response.is_success and payload.get("ok") is True:
            external_id = str(payload.get("result", {}).get("message_id", "")) or None
            return True, external_id, None

        description = payload.get("description")
        if not description:
            description = f"HTTP {response.status_code}"
        return False, None, f"Eitaa publish failed: {description}"

    def publish(self, article: Article) -> PublishResult:
        success, external_id, error = self._request(self.render(article))
        return PublishResult(
            success=success,
            destination=self.name,
            external_id=external_id,
            error=error,
        )
