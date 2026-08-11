"""Telegram publisher."""

from .webhooks import WebhookPublisher


class TelegramPublisher(WebhookPublisher):
    """Publish via Telegram Bot API compatible endpoint."""
