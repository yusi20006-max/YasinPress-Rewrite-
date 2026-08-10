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
