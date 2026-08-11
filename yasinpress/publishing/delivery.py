from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult
from yasinpress.transport.http import HTTPTransport


class PayloadPublisher(Publisher, Protocol):
    def render(self, article: Article) -> str: ...


@dataclass(frozen=True)
class DeliveryTarget:
    name: str
    url: str
    content_type: str = "text/plain; charset=utf-8"


class HTTPDelivery:
    """Turn a rendered Publisher payload into an HTTP delivery without leaking transport into domain code."""

    def __init__(self, transport: HTTPTransport) -> None:
        self.transport = transport

    def deliver(
        self, publisher: PayloadPublisher, article: Article, target: DeliveryTarget
    ) -> PublishResult:
        payload = publisher.render(article)
        response = self.transport.post_text(
            target.url,
            payload,
            headers={"Content-Type": target.content_type},
        )
        if response.ok:
            return PublishResult(True, target.name, external_id=article.id)
        return PublishResult(
            False,
            target.name,
            external_id=article.id,
            error=f"HTTP {response.status_code}: {response.body}",
        )
