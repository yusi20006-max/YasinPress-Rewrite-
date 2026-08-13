from yasinpress.fetch.feed import FeedFetcher

RSS = """<rss><channel><item><title>Test</title><link>https://example.com/a</link><description>Hello</description></item></channel></rss>"""


def test_feed_fetcher_parses_rss_without_network():
    calls = []

    def fake_fetch(url: str, *, timeout: float) -> str:
        calls.append((url, timeout))
        return RSS

    result = FeedFetcher(fetch=fake_fetch, timeout=7).fetch_url("https://news.example/feed.xml")
    assert result.source == "news.example"
    assert len(result.items) == 1
    assert result.items[0].title == "Test"
    assert calls == [("https://news.example/feed.xml", 7)]


def test_fetch_many_isolates_source_failures():
    def fake_fetch(url: str, *, timeout: float) -> str:
        if "down.example" in url:
            raise OSError("connection failed")
        return RSS

    results = FeedFetcher(fetch=fake_fetch).fetch_many(
        ("https://down.example/rss", "https://ok.example/rss")
    )

    assert len(results) == 2
    assert results[0].items == ()
    assert results[0].error is not None
    assert results[1].error is None
    assert len(results[1].items) == 1


def test_fetch_many_isolates_parse_failures():
    def fake_fetch(url: str, *, timeout: float) -> str:
        if "bad.example" in url:
            return "<not-valid-rss>"
        return RSS

    results = FeedFetcher(fetch=fake_fetch).fetch_many(
        ("https://bad.example/rss", "https://ok.example/rss")
    )

    assert results[0].error is not None
    assert results[1].error is None
    assert results[1].items
