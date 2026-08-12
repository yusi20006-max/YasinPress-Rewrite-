from datetime import UTC, datetime, timedelta

from yasinpress.processing.freshness import is_fresh
from yasinpress.sources.feed import parse_rss
from yasinpress.sources.manager import Source, SourceManager, ingest_source


def test_missing_timestamps_fallback():
    # If a feed item has no publication date, _published_at defaults to current time
    # Let's test that parse_rss parses empty/missing pubDate correctly.
    xml = """<rss><channel><item><title>Test Item</title><link>https://example.com/item</link><description>Content</description></item></channel></rss>"""
    items = parse_rss(xml)
    assert len(items) == 1
    assert items[0].published_at is not None
    # Within 1 minute of now
    assert (datetime.now(UTC) - items[0].published_at).total_seconds() < 60


def test_timezone_conversion_and_naive():
    # Timezone conversion: pubDate with timezone offsets
    xml_tz = """<rss><channel><item>
        <title>TZ Item</title>
        <link>https://example.com/tz</link>
        <description>Content</description>
        <pubDate>Tue, 11 Aug 2026 14:30:00 +0330</pubDate>
    </item></channel></rss>"""
    items = parse_rss(xml_tz)
    assert len(items) == 1
    # 14:30:00 +03:30 should be converted to 11:00:00 UTC
    assert items[0].published_at.tzinfo == UTC
    assert items[0].published_at == datetime(2026, 8, 11, 11, 0, 0, tzinfo=UTC)


def test_stale_items_detection():
    # A feed that only has items older than 24h is stale -> status "degraded", stale_count incremented
    source = Source("StaleSource", "https://example.com/stale")

    # 25 hours ago pubDate
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
    # Ingesting from a source that fails
    source = Source("FailSource", "https://example.com/fail")

    def failing_fetch(url):
        raise ValueError("Network Error")

    # 1st failure
    items = ingest_source(source, failing_fetch)
    assert len(items) == 0
    assert source.status == "degraded"
    assert source.consecutive_failures == 1
    assert source.failure_count == 1
    assert source.enabled is True

    # 2nd failure
    ingest_source(source, failing_fetch)
    assert source.status == "degraded"
    assert source.consecutive_failures == 2
    assert source.enabled is True

    # 3rd failure -> disabled, failed
    ingest_source(source, failing_fetch)
    assert source.status == "failed"
    assert source.consecutive_failures == 3
    assert source.enabled is False

    # Attempt ingest while disabled should return empty and do nothing
    items_disabled = ingest_source(source, failing_fetch)
    assert len(items_disabled) == 0

    # Let's recover: manual override or fetch succeeds (if we temporarily set enabled = True to retry)
    source.enabled = True
    success_xml = """<rss><channel><item><title>Fresh</title><link>https://example.com/fresh</link><description>Content</description></item></channel></rss>"""
    items_recovered = ingest_source(source, lambda url: success_xml)
    assert len(items_recovered) == 1
    assert source.status == "healthy"
    assert source.consecutive_failures == 0
    assert source.enabled is True


def test_multi_source_ingestion_independent_failure():
    # If one source fails, other sources must still be processed (no global failure)
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
        items = ingest_source(src, multi_fetch)
        results.extend(items)

    assert len(results) == 2  # GoodSource and GoodSource2 succeeded
    assert source1.status == "healthy"
    assert source1.success_count == 1

    assert source2.status == "degraded"
    assert source2.failure_count == 1

    assert source3.status == "healthy"
    assert source3.success_count == 1


def test_breaking_news_exemption():
    # Test breaking/urgent exception logic
    now = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)

    # Normal article older than 12h: rejected
    assert not is_fresh(now - timedelta(hours=13), now=now, is_breaking=False)

    # Breaking article older than 12h but <= 24h: accepted
    assert is_fresh(now - timedelta(hours=13), now=now, is_breaking=True)
    assert is_fresh(now - timedelta(hours=24), now=now, is_breaking=True)

    # Breaking article > 24h: rejected
    assert not is_fresh(now - timedelta(hours=25), now=now, is_breaking=True)
