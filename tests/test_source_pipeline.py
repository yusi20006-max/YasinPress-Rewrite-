from datetime import UTC, datetime, timedelta

from yasinpress.processing.freshness import is_fresh
from yasinpress.sources.feed import parse_rss
from yasinpress.sources.manager import Source, SourceManager, ingest_source


def test_missing_timestamps_fallback():
    xml = """<rss><channel><item><title>Test Item</title><link>https://example.com/item</link><description>Content</description></item></channel></rss>"""
    items = parse_rss(xml)
    assert len(items) == 1
    assert items[0].published_at == datetime.fromtimestamp(0, tz=UTC)


def test_timezone_conversion_and_naive():
    xml_tz = """<rss><channel><item>
        <title>TZ Item</title>
        <link>https://example.com/tz</link>
        <description>Content</description>
        <pubDate>Tue, 11 Aug 2026 14:30:00 +0330</pubDate>
    </item></channel></rss>"""
    items = parse_rss(xml_tz)
    assert len(items) == 1
    assert items[0].published_at.tzinfo == UTC
    assert items[0].published_at == datetime(2026, 8, 11, 11, 0, 0, tzinfo=UTC)


def test_stale_items_detection():
    source = Source("StaleSource", "https://example.com/stale")
    old_time = (datetime.now(UTC) - timedelta(hours=25)).strftime("%a, %d %b %Y %H:%M:%S UTC")
    stale_xml = f"""<rss><channel><item>
        <title>Stale Item</title>
        <link>https://example.com/stale-item</link>
        <description>Content</description>
        <pubDate>{old_time}</pubDate>
    </item></channel></rss>"""

    items = ingest_source(source, lambda url: stale_xml)
    assert len(items) == 1
    assert source.status == "degraded"
    assert source.stale_count == 1
    assert source.success_count == 1


def test_source_failure_and_recovery():
    source = Source("FailSource", "https://example.com/fail")

    def failing_fetch(url):
        raise ValueError("Network Error")

    ingest_source(source, failing_fetch)
    assert source.status == "degraded"
    assert source.consecutive_failures == 1
    assert source.failure_count == 1
    assert source.enabled is True

    ingest_source(source, failing_fetch)
    assert source.status == "degraded"
    assert source.consecutive_failures == 2
    assert source.enabled is True

    ingest_source(source, failing_fetch)
    assert source.status == "failed"
    assert source.consecutive_failures == 3
    assert source.enabled is False

    items_disabled = ingest_source(source, failing_fetch)
    assert len(items_disabled) == 0

    source.enabled = True
    success_xml = """<rss><channel><item><title>Fresh</title><link>https://example.com/fresh</link><description>Content</description></item></channel></rss>"""
    items_recovered = ingest_source(source, lambda url: success_xml)
    assert len(items_recovered) == 1
    assert source.status == "healthy"
    assert source.consecutive_failures == 0
    assert source.enabled is True


def test_multi_source_ingestion_independent_failure():
    source1 = Source("GoodSource", "https://example.com/good")
    source2 = Source("BadSource", "https://example.com/bad")
    source3 = Source("GoodSource2", "https://example.com/good2")

    manager = SourceManager([source1, source2, source3])
    good_xml = """<rss><channel><item><title>Fresh</title><link>https://example.com/fresh</link><description>Content</description></item></channel></rss>"""

    def multi_fetch(url):
        if "bad" in url:
            raise RuntimeError("DNS lookup failed")
        return good_xml

    results = []
    for src in manager.enabled():
        results.extend(ingest_source(src, multi_fetch))

    assert len(results) == 2
    assert source1.status == "healthy"
    assert source1.success_count == 1
    assert source2.status == "degraded"
    assert source2.failure_count == 1
    assert source3.status == "healthy"
    assert source3.success_count == 1


def test_articles_older_than_twelve_hours_are_never_fresh_including_breaking():
    now = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
    assert is_fresh(now - timedelta(hours=11, minutes=59), now=now)
    assert is_fresh(now - timedelta(hours=12), now=now)
    assert not is_fresh(now - timedelta(hours=13), now=now, is_breaking=True)
    assert not is_fresh(now - timedelta(hours=24), now=now, is_breaking=True)
