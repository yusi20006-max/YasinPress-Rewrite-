from datetime import datetime, timezone

from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.pipeline.application import YasinPressApplication
from yasinpress.sources.feed import FeedItem


class FakeAI:
    def rewrite(self, text: str, **kwargs) -> str:
        return "REWRITTEN: " + text


def test_feed_item_reaches_persistent_article_store(tmp_path):
    db = SQLiteRepositories(str(tmp_path / "e2e.db"))
    app = YasinPressApplication(ai=FakeAI(), repositories=db)
    item = FeedItem("Title", "https://example.com/1", "body", datetime.now(timezone.utc))
    report = app.process_items([item])
    assert report.persisted_count == 1
    assert db.articles.get("https://example.com/1") is not None
    db.close()
