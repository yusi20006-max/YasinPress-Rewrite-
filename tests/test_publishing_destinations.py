from datetime import datetime, timezone
import json

from yasinpress.database.models import Article
from yasinpress.publishing import PublishResult
from yasinpress.publishing.eitaa import EitaaPublisher
from yasinpress.publishing.pwa import PWAPublisher
from yasinpress.publishing.rss import RSSPublisher


def article() -> Article:
    return Article("1", "خبر تست", "https://example.com/1", "محتوا", "test", datetime.now(timezone.utc), "technology")


def test_all_destination_adapters_share_contract():
    a = article()
    rss = RSSPublisher()
    pwa = PWAPublisher()
    eitaa = EitaaPublisher(channel="news")
    assert rss.publish(a).success
    assert pwa.publish(a).success
    assert eitaa.publish(a).success
    assert isinstance(rss.publish(a), PublishResult)
    assert "<title>خبر تست</title>" in rss.render(a)
    assert json.loads(pwa.render(a))["id"] == "1"
    assert "https://example.com/1" in eitaa.render(a)
