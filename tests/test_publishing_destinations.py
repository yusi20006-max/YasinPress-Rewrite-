import json
from datetime import UTC, datetime
from pathlib import Path

from yasinpress.database.models import Article
from yasinpress.publishing import PublishResult
from yasinpress.publishing.eitaa import EitaaPublisher
from yasinpress.publishing.pwa import PWAPublisher
from yasinpress.publishing.rss import RSSPublisher


def article(article_id: str = "1", title: str = "خبر تست") -> Article:
    return Article(
        article_id,
        title,
        f"https://example.com/{article_id}",
        "محتوا",
        "test",
        datetime.now(UTC),
        "technology",
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


def test_pwa_publisher_persists_json_feed(tmp_path: Path):
    output = tmp_path / "pwa" / "feed.json"
    publisher = PWAPublisher(
        output_path=output,
        title="YasinPress PWA",
        feed_url="https://example.test/feed.json",
    )

    publisher.publish(article("1", "اول"))
    publisher.publish(article("2", "دوم"))

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["version"] == "https://jsonfeed.org/version/1.1"
    assert payload["title"] == "YasinPress PWA"
    assert payload["language"] == "fa"
    assert payload["feed_url"] == "https://example.test/feed.json"
    assert [item["id"] for item in payload["items"]] == ["2", "1"]
    assert payload["items"][0]["author"]["name"] == "test"
    assert payload["items"][0]["tags"] == ["technology"]


def test_pwa_ai_modified_item_exposes_modified_date():
    published = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)
    received = datetime(2026, 8, 10, 10, 5, tzinfo=UTC)
    a = Article(
        "ai-1",
        "بازنویسی شده",
        "https://example.com/ai-1",
        "محتوا",
        "BBC Persian",
        published,
        "news",
        ai_modified=True,
        received_at=received,
    )
    item = json.loads(PWAPublisher().render(a))
    assert item["date_published"] == published.isoformat()
    assert item["date_modified"] == received.isoformat()
    assert item["author"]["name"] == "BBC Persian"


def test_rss_publisher_persists_rss20_feed(tmp_path: Path):
    output = tmp_path / "rss" / "feed.xml"
    publisher = RSSPublisher(
        output_path=output,
        title="YasinPress RSS",
        link="https://example.test/",
        feed_url="https://example.test/feed.xml",
    )

    publisher.publish(article("1", "اول"))
    publisher.publish(article("2", "دوم"))

    xml = output.read_text(encoding="utf-8")
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert '<rss version="2.0">' in xml
    assert "<title>YasinPress RSS</title>" in xml
    assert "<language>fa</language>" in xml
    assert "<lastBuildDate>" in xml
    assert "<source>test</source>" in xml
    assert "<title>دوم</title>" in xml
    assert "<title>اول</title>" in xml


def test_publishers_replace_existing_item_by_id(tmp_path: Path):
    pwa_output = tmp_path / "feed.json"
    rss_output = tmp_path / "feed.xml"
    pwa = PWAPublisher(output_path=pwa_output)
    rss = RSSPublisher(output_path=rss_output)

    pwa.publish(article("1", "نسخه اول"))
    pwa.publish(article("1", "نسخه جدید"))
    rss.publish(article("1", "نسخه اول"))
    rss.publish(article("1", "نسخه جدید"))

    payload = json.loads(pwa_output.read_text(encoding="utf-8"))
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"] == "نسخه جدید"
    xml = rss_output.read_text(encoding="utf-8")
    assert xml.count("<guid isPermaLink=\"true\">https://example.com/1</guid>") == 1
    assert "نسخه جدید" in xml
