from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.publishing import Publisher, PublishResult
from yasinpress.publishing.orchestrator import PublishingOrchestrator
from yasinpress.publishing.reliability import RetryPolicy


class GoodPublisher(Publisher):
    @property
    def name(self) -> str:
        return "good"

    def publish(self, article: Article) -> PublishResult:
        return PublishResult(True, self.name, external_id=article.id)


class FailingPublisher(Publisher):
    @property
    def name(self) -> str:
        return "failing"

    def publish(self, article: Article) -> PublishResult:
        raise RuntimeError("destination unavailable")


def article() -> Article:
    return Article(
        id="1",
        title="خبر",
        url="https://example.com/1",
        content="محتوا",
        source="test",
        published_at=datetime.now(UTC),
    )


def test_one_publisher_failure_does_not_block_other_destinations():
    report = PublishingOrchestrator([FailingPublisher(), GoodPublisher()]).publish(article())
    assert len(report.results) == 2
    assert not report.results[0].success
    assert report.results[1].success
    assert report.success_count == 1


def test_successful_destination_is_not_retried_when_another_destination_fails():
    report = PublishingOrchestrator(
        [GoodPublisher(), FailingPublisher()],
        retry_policy=RetryPolicy(max_attempts=1),
    )

    first = report.publish(article())
    second = report.publish(article())

    assert first.results[0].success
    assert first.results[1].success is False
    assert second.results[0].skipped is True
    assert second.results[1].success is False
    assert second.results[1].skipped is False


def test_updated_at_and_published_at_share_canonical_delivery_version():
    publisher = GoodPublisher()
    orchestrator = PublishingOrchestrator([publisher])
    published = datetime(2026, 8, 15, 10, tzinfo=UTC)
    updated = datetime(2026, 8, 15, 11, tzinfo=UTC)

    first = Article(
        id="versioned",
        title="نسخه اول",
        url="https://example.com/versioned",
        content="اول",
        source="test",
        published_at=published,
    )
    updated_article = Article(
        id="versioned",
        title="نسخه دوم",
        url="https://example.com/versioned",
        content="دوم",
        source="test",
        published_at=published,
        updated_at=updated,
    )

    first_report = orchestrator.publish(first)
    second_report = orchestrator.publish(updated_article)
    third_report = orchestrator.publish(updated_article)

    assert first_report.results[0].success
    assert second_report.results[0].success
    assert second_report.results[0].skipped is False
    assert third_report.results[0].skipped is True
