from datetime import UTC, datetime

import httpx

from yasinpress.database.models import Article
from yasinpress.database.sqlite import SQLiteDeliveryHistory, SQLiteIdempotencyStore
from yasinpress.publishing import Publisher, PublishResult
from yasinpress.publishing.eitaa import EitaaPublisher
from yasinpress.publishing.history import DeliveryRecord, InMemoryDeliveryHistory
from yasinpress.publishing.idempotency import IdempotencyStore
from yasinpress.publishing.orchestrator import PublishingOrchestrator
from yasinpress.publishing.reliability import ReliablePublisher, RetryPolicy


class MockPublisher(Publisher):
    @property
    def name(self) -> str:
        return "mock"

    def publish(self, article: Article) -> PublishResult:
        return PublishResult(True, self.name, external_id=article.id)


class FlakyPublisher(Publisher):
    name = "flaky"

    def __init__(self, failures: int):
        self.failures = failures
        self.calls = 0

    def publish(self, article: Article) -> PublishResult:
        self.calls += 1
        if self.calls <= self.failures:
            return PublishResult(False, self.name, external_id=article.id, error="temporary")
        return PublishResult(True, self.name, external_id=article.id)


ARTICLE = Article("1", "title", "https://example.com/1", "body", "test", datetime.now(UTC))


def test_publisher_contract():
    result = MockPublisher().publish(ARTICLE)
    assert result.success
    assert result.destination == "mock"
    assert result.external_id == "1"


def test_eitaa_publisher_sends_message(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True, "result": {"message_id": 42}}

    def fake_post(url, *, data, timeout):
        captured.update(url=url, data=data, timeout=timeout)
        return Response()

    monkeypatch.setattr(httpx, "post", fake_post)
    result = EitaaPublisher(token="bot-token", channel="123").publish(ARTICLE)

    assert result.success
    assert result.destination == "eitaa"
    assert result.external_id == "42"
    assert captured["url"] == "https://eitaayar.ir/api/bot-token/sendMessage"
    assert captured["data"]["chat_id"] == "123"
    assert captured["data"]["text"] == "<b>title</b>\n\nbody\n\nمنبع: example.com"
    assert "https://example.com/1" not in captured["data"]["text"]


def test_eitaa_publisher_reports_api_rejection(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": False, "error": "invalid token"}

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: Response())
    result = EitaaPublisher(token="bad", channel="123").publish(ARTICLE)

    assert not result.success
    assert result.destination == "eitaa"
    assert "invalid token" in (result.error or "")


def test_eitaa_publisher_reports_transport_failure(monkeypatch):
    def fake_post(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "post", fake_post)
    result = EitaaPublisher(token="token", channel="123").publish(ARTICLE)

    assert not result.success
    assert "request failed" in (result.error or "")


def test_reliable_publisher_retries_and_succeeds():
    publisher = FlakyPublisher(2)
    retry = ReliablePublisher(publisher, RetryPolicy(3, 0, 0), sleeper=lambda _: None)
    assert retry.publish(ARTICLE).success
    assert publisher.calls == 3
    assert retry.attempts == 3


def test_orchestrator_is_idempotent_after_success():
    publisher = FlakyPublisher(0)
    history = InMemoryDeliveryHistory()
    orchestrator = PublishingOrchestrator([publisher], retry_policy=RetryPolicy(1), history=history, idempotency=IdempotencyStore())
    assert orchestrator.publish(ARTICLE).success_count == 1
    assert orchestrator.publish(ARTICLE).success_count == 1
    assert publisher.calls == 1
    assert len(history.all()) == 1


def test_sqlite_publishing_state():
    import sqlite3

    conn = sqlite3.connect(":memory:")
    history = SQLiteDeliveryHistory(conn)
    history.add(DeliveryRecord("1", "mock", True, 1, "1", None))
    assert history.for_article("1")[0].success
    store = SQLiteIdempotencyStore(conn)
    assert not store.seen("1:mock")
    store.mark("1:mock")
    store.mark("1:mock")
    assert store.seen("1:mock")
