from datetime import datetime, timezone

import httpx

from yasinpress.database.models import Article
from yasinpress.publishing.rss import RSSPublisher
from yasinpress.publishing.delivery import DeliveryTarget, HTTPDelivery
from yasinpress.transport.http import HTTPTransport


def article() -> Article:
    return Article(
        id="1",
        title="خبر تست",
        url="https://example.com/1",
        content="محتوا",
        source="test",
        published_at=datetime.now(timezone.utc),
    )


def test_http_delivery_success():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201, text="created", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with HTTPTransport(client=client) as transport:
        result = HTTPDelivery(transport).deliver(
            RSSPublisher(), article(), DeliveryTarget("rss-api", "https://example.test/publish", "application/xml")
        )
    assert result.success
    assert result.external_id == "1"
    assert requests[0].headers["content-type"] == "application/xml"
    assert "<title>خبر تست</title>" in requests[0].content.decode()


def test_http_delivery_converts_non_2xx_to_result():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with HTTPTransport(client=client) as transport:
        result = HTTPDelivery(transport).deliver(
            RSSPublisher(), article(), DeliveryTarget("rss-api", "https://example.test/publish")
        )
    assert not result.success
    assert "503" in (result.error or "")
