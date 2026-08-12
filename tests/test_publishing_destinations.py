import json
from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.publishing import PublishResult
from yasinpress.publishing.eitaa import EitaaPublisher
from yasinpress.publishing.pwa import PWAPublisher
from yasinpress.publishing.rss import RSSPublisher


def article() -> Article:
    return Article(
        "1", "خبر تست", "https://example.com/1", "محتوا", "test", datetime.now(UTC), "technology"
    )


def test_all_destination_adapters_share_contract():
    a = article()
    rss = RSSPublisher()
    pwa = PWAPublisher()
    eitaa = EitaaPublisher(token="test-token", channel="news")
    assert rss.publish(a).success
    assert pwa.publish(a).success
    assert isinstance(eitaa.render(a), str)
    assert isinstance(rss.publish(a), PublishResult)
    assert "<title>خبر تست</title>" in rss.render(a)
    assert json.loads(pwa.render(a))["id"] == "1"
    assert "منبع: example.com" in eitaa.render(a)
