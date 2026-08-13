from datetime import UTC, datetime, timedelta

import pytest

from yasinpress.database.models import Article, PublicationJob
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.queue_processor import PublicationQueueProcessor


class MockPublisher:
    def __init__(self, name: str, success: bool = True) -> None:
        self._name = name
        self.success = success
        self.published_articles = []

    @property
    def name(self) -> str:
        return self._name

    def publish(self, article: Article) -> PublishResult:
        self.published_articles.append(article)
        if self.success:
            return PublishResult(True, self.name, external_id=article.id)
        return PublishResult(False, self.name, error="Failed to publish")


@pytest.fixture
def repo():
    r = SQLiteRepositories(":memory:")
    yield r
    r.close()


def create_test_article(repo: SQLiteRepositories, id_: str, source: str, title: str = "test") -> Article:
    art = Article(
        id=id_, title=title, url=f"https://example.com/{source}/{id_}",
        content="content", source=source, published_at=datetime.now(UTC),
    )
    repo.articles.save(art)
    return art


def test_persistence_across_restart(tmp_path):
    db_file = str(tmp_path / "test_restart.db")
    repo1 = SQLiteRepositories(db_file)
    create_test_article(repo1, "art1", "sourceA")
    repo1.publication_queue.add_job(PublicationJob("art1:pwa", "art1", "pwa", "pending", 10, "normal", "sourceA"))
    repo1.close()
    repo2 = SQLiteRepositories(db_file)
    loaded = repo2.publication_queue.get_job("art1:pwa")
    assert loaded is not None
    assert loaded.status == "pending"
    assert loaded.source == "sourceA"
    repo2.close()


def test_queue_metrics(repo):
    for job in [
        PublicationJob("j1", "a1", "dest1", "pending", 10, "normal", "src1"),
        PublicationJob("j2", "a2", "dest1", "pending", 10, "normal", "src1"),
        PublicationJob("j3", "a3", "dest1", "processing", 10, "normal", "src1"),
        PublicationJob("j4", "a4", "dest1", "succeeded", 10, "normal", "src1"),
        PublicationJob("j5", "a5", "dest1", "dead_letter", 10, "normal", "src1"),
    ]:
        repo.publication_queue.add_job(job)
    metrics = repo.publication_queue.get_metrics()
    assert metrics["pending"] == 2
    assert metrics["processing"] == 1
    assert metrics["dead_letter"] == 1
    assert metrics["published"] == 1
    assert metrics["queue_depth"] == 3


def test_stale_lease_recovery(repo):
    now = datetime.now(UTC)
    repo.publication_queue.add_job(PublicationJob("expired_job", "a1", "pwa", "processing", 10, "normal", "src", attempts=1, lease_expires_at=now - timedelta(seconds=10)))
    repo.publication_queue.add_job(PublicationJob("active_job", "a2", "pwa", "processing", 10, "normal", "src", attempts=1, lease_expires_at=now + timedelta(seconds=10)))
    processor = PublicationQueueProcessor(repo, [])
    assert processor.recover_expired_leases(now) == 1
    assert repo.publication_queue.get_job("expired_job").status == "retrying"
    assert repo.publication_queue.get_job("expired_job").lease_expires_at is None
    assert repo.publication_queue.get_job("active_job").status == "processing"


def test_global_and_source_rate_limits(repo):
    now = datetime.now(UTC)
    for source in ("sourceA", "sourceB"):
        for i in range(1, 7):
            article_id = f"a_{source}_{i}"
            create_test_article(repo, article_id, source)
            repo.publication_queue.add_job(PublicationJob(f"{article_id}:pwa", article_id, "pwa", "pending", 10, "normal", source))
    publisher = MockPublisher("pwa")
    processor = PublicationQueueProcessor(repo, [publisher], max_global_per_hour=30, max_source_per_hour=5)
    processor.process_cycle(now)
    assert len(publisher.published_articles) == 10
    assert sum(a.source == "sourceA" for a in publisher.published_articles) == 5
    assert sum(a.source == "sourceB" for a in publisher.published_articles) == 5
    processor.process_cycle(now + timedelta(minutes=10))
    assert len(publisher.published_articles) == 10


def test_global_limit_is_thirty_per_rolling_hour(repo):
    now = datetime.now(UTC)
    publisher = MockPublisher("pwa")
    processor = PublicationQueueProcessor(repo, [publisher], max_global_per_hour=30, max_source_per_hour=30)
    for i in range(30):
        article_id = f"cap_{i}"
        create_test_article(repo, article_id, f"source_{i}")
        repo.publication_queue.add_job(PublicationJob(f"{article_id}:pwa", article_id, "pwa", "pending", 10, "normal", f"source_{i}"))
    processor.process_cycle(now)
    assert len(publisher.published_articles) == 30
    article_id = "cap_30"
    create_test_article(repo, article_id, "source_30")
    repo.publication_queue.add_job(PublicationJob(f"{article_id}:pwa", article_id, "pwa", "pending", 10, "normal", "source_30"))
    assert processor.process_cycle(now + timedelta(minutes=10)) == []


def test_global_capacity_opens_after_rolling_hour(repo):
    now = datetime.now(UTC)
    publisher = MockPublisher("pwa")
    processor = PublicationQueueProcessor(repo, [publisher], max_global_per_hour=30, max_source_per_hour=30)
    for i in range(30):
        article_id = f"window_{i}"
        create_test_article(repo, article_id, f"source_{i}")
        repo.publication_queue.add_job(PublicationJob(f"{article_id}:pwa", article_id, "pwa", "pending", 10, "normal", f"source_{i}"))
    processor.process_cycle(now)
    article_id = "window_30"
    create_test_article(repo, article_id, "source_30")
    repo.publication_queue.add_job(PublicationJob(f"{article_id}:pwa", article_id, "pwa", "pending", 10, "normal", "source_30"))
    assert len(processor.process_cycle(now + timedelta(hours=1, seconds=1))) == 1


def test_fair_scheduling_and_priority_ordering(repo):
    now = datetime.now(UTC)
    for i in range(1, 16):
        create_test_article(repo, f"a_{i}", "sourceA")
        repo.publication_queue.add_job(PublicationJob(f"a_{i}:pwa", f"a_{i}", "pwa", "pending", 10, "normal", "sourceA", created_at=now - timedelta(minutes=i)))
    for i in range(1, 3):
        create_test_article(repo, f"b_{i}", "sourceB")
        repo.publication_queue.add_job(PublicationJob(f"b_{i}:pwa", f"b_{i}", "pwa", "pending", 10, "normal", "sourceB", created_at=now - timedelta(minutes=i)))
    create_test_article(repo, "c_high", "sourceC")
    repo.publication_queue.add_job(PublicationJob("c_high:pwa", "c_high", "pwa", "pending", 40, "breaking", "sourceC"))
    publisher = MockPublisher("pwa")
    processor = PublicationQueueProcessor(repo, [publisher], max_global_per_hour=4, max_source_per_hour=5)
    processor.process_cycle(now)
    published_ids = [a.id for a in publisher.published_articles]
    assert "c_high" in published_ids
    assert len(published_ids) == 4
    assert any(id_.startswith("b_") for id_ in published_ids)
    assert any(id_.startswith("a_") for id_ in published_ids)


def test_retry_backoff_and_dead_letter(repo):
    now = datetime.now(UTC)
    create_test_article(repo, "fail_art", "src")
    repo.publication_queue.add_job(PublicationJob("fail_art:pwa", "fail_art", "pwa", "pending", 10, "normal", "src", max_attempts=3))
    processor = PublicationQueueProcessor(repo, [MockPublisher("pwa", success=False)], base_backoff_seconds=10.0)
    processor.process_cycle(now)
    job = repo.publication_queue.get_job("fail_art:pwa")
    assert job.status == "retrying" and job.attempts == 1
    assert job.next_attempt_at == now + timedelta(seconds=10)
    processor.process_cycle(now + timedelta(seconds=5))
    assert repo.publication_queue.get_job("fail_art:pwa").attempts == 1
    processor.process_cycle(now + timedelta(seconds=11))
    job = repo.publication_queue.get_job("fail_art:pwa")
    assert job.status == "retrying" and job.attempts == 2
    assert job.next_attempt_at == now + timedelta(seconds=31)
    processor.process_cycle(now + timedelta(seconds=32))
    job = repo.publication_queue.get_job("fail_art:pwa")
    assert job.status == "dead_letter" and job.attempts == 3


def test_concurrent_worker_safety(repo):
    now = datetime.now(UTC)
    create_test_article(repo, "a1", "src")
    repo.publication_queue.add_job(PublicationJob("a1:pwa", "a1", "pwa", "processing", 10, "normal", "src", lease_expires_at=now + timedelta(seconds=30)))
    publisher = MockPublisher("pwa")
    processor = PublicationQueueProcessor(repo, [publisher])
    processor.process_cycle(now)
    assert len(publisher.published_articles) == 0
