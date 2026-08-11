from __future__ import annotations

from yasinpress.cli.main import _startup_feed_setup
from yasinpress.sources.catalog import RSSFeed


def test_startup_uses_active_feeds_when_none_configured(monkeypatch):
    monkeypatch.delenv("YASINPRESS_FEEDS", raising=False)
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    monkeypatch.setattr(
        "yasinpress.cli.main.active_feeds",
        lambda: (RSSFeed("Test RSS", "https://example.com/feed.xml"),),
    )

    _startup_feed_setup()

    assert __import__("os").environ["YASINPRESS_FEEDS"] == "https://example.com/feed.xml"


def test_startup_allows_custom_feed(monkeypatch):
    monkeypatch.delenv("YASINPRESS_FEEDS", raising=False)
    answers = iter(["y", "https://example.com/custom.xml"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(
        "yasinpress.cli.main.active_feeds",
        lambda: (RSSFeed("Test RSS", "https://example.com/feed.xml"),),
    )

    _startup_feed_setup()

    assert __import__("os").environ["YASINPRESS_FEEDS"] == (
        "https://example.com/feed.xml,https://example.com/custom.xml"
    )
