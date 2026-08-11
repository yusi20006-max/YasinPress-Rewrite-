"""Webhook publisher."""

import httpx


class WebhookPublisher:
    """Publishes messages to generic webhooks."""

    def __init__(self, url: str) -> None:
        self.url = url

    def publish(self, message: str) -> bool:
        """Post a message payload."""
        response = httpx.post(self.url, json={"message": message}, timeout=10)
        return response.is_success
