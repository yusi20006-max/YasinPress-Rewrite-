from datetime import datetime, timezone

from yasinpress.database.models import Article
from yasinpress.publishing import PublishResult, Publisher


class MockPublisher(Publisher):
    @property
    def name(self) -> str:
        return "mock"

    def publish(self, article: Article) -> PublishResult:
        return PublishResult(True, self.name, external_id=article.id)


def test_publisher_contract():
    article = Article(
        id="1",
        title="خبر",
        url="https://example.com/1",
        content="متن",
        source="test",
        published_at=datetime.now(timezone.utc),
    )
    result = MockPublisher().publish(article)
    assert result.success
    assert result.destination == "mock"
    assert result.external_id == "1"
