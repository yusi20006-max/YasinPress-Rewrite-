from datetime import UTC, datetime
from unittest.mock import Mock, patch

from yasinpress.database.models import Article
from yasinpress.publishing.eitaa import EitaaPublisher


def article() -> Article:
    return Article(
        id="YP-000002",
        title="خبر آزمایشی",
        url="https://example.com/news/2",
        content="متن خبر",
        source="example.com",
        published_at=datetime.now(UTC),
    )


def test_publish_success_returns_external_message_id():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"ok": True, "result": {"message_id": 123}}
    with patch("yasinpress.publishing.eitaa.httpx.post", return_value=response) as post:
        result = EitaaPublisher(token="token", channel="channel").publish(article())
    assert result.success
    assert result.external_id == "123"
    post.assert_called_once()


def test_publish_rejected_api_returns_failure():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"ok": False, "error": "bad token"}
    with patch("yasinpress.publishing.eitaa.httpx.post", return_value=response):
        result = EitaaPublisher(token="token", channel="channel").publish(article())
    assert not result.success
    assert "bad token" in (result.error or "")
