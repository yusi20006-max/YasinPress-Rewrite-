from datetime import UTC, datetime

from yasinpress.pipeline.application import YasinPressApplication


class Item:
    def __init__(self, title: str, url: str, content: str) -> None:
        self.title = title
        self.url = url
        self.content = content
        self.source = "test"
        self.published_at = datetime.now(UTC)
        self.category = "tech"


def test_application_persists_processed_articles():
    app = YasinPressApplication()
    report = app.process_items([Item("خبر", "https://example.com/1", "محتوا")])
    assert report.persisted_count == 1
    assert app.get_article("https://example.com/1") is not None
    app.close()
