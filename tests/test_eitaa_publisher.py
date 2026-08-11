from datetime import UTC, datetime

import httpx

from yasinpress.database.models import Article
from yasinpress.publishing.eitaa import EitaaPublisher


ARTICLE = Article(
    "1",
    "عنوان خبر",
    "https://example.com/1",
    "متن خبر",
    "bbc",
    datetime.now(UTC),
)


def test_eitaa_publisher_sends_message():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["form"] = dict(httpx.QueryParams(request.content.decode()))
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 42}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    publisher = EitaaPublisher(
        channel="@yasinpress",
        token="test-token",
        base_url="https://eitaayar.test/api",
        client=client,
    )

    result = publisher.publish(ARTICLE)

    assert result.success is True
    assert result.destination == "eitaa"
    assert result.external_id == "42"
    assert captured["url"] == "https://eitaayar.test/api/test-token/sendMessage"
    assert captured["form"] == {
        "chat_id": "@yasinpress",
        "text": "عنوان خبر\n\nمتن خبر\n\nhttps://example.com/1",
    }
    client.close()


def test_eitaa_publisher_reports_api_failure():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": False, "description": "Unauthorized"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    publisher = EitaaPublisher(
        channel="@yasinpress",
        token="test-token",
        base_url="https://eitaayar.test/api",
        client=client,
    )

    result = publisher.publish(ARTICLE)

    assert result.success is False
    assert result.destination == "eitaa"
    assert result.error == "Eitaa publish failed: Unauthorized"
    client.close()
