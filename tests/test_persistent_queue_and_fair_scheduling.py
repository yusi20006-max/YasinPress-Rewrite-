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
    # Use memory database for deterministic isolated tests
    r = SQLiteRepositories(":memory:")
    yield r
    r.close()


def create_test_article(
    repo: SQLiteRepositories, id_: str, source: str, title: str = "test"
) -> Article:
    art = Article(
        id=id_,
        title=title,
        url=f"https://example.com/{source}/{id_}",
        content="content",
        source=source,
        published_at=datetime.now(UTC),
    )
    repo.articles.save(art)
    return art


def test_persistence_across_restart(tmp_path):
    db_file = str(tmp_path / "test_restart.db")

    # Session 1: Create and queue jobs
    repo1 = SQLiteRepositories(db_file)
    create_test_article(repo1, "art1", "sourceA")
    job = PublicationJob(
        id="art1:pwa",
        article_id="art1",
        destination="pwa",
        status="pending",
        priority=10,
        priority_level="normal",
        source="sourceA",
    )
    repo1.publication_queue.add_job(job)
    repo1.close()

    # Session 2: Reload and verify jobs survive
    repo2 = SQLiteRepositories(db_file)
    loaded = repo2.publication_queue.get_job("art1:pwa")
    assert loaded is not None
    assert loaded.status == "pending"
    assert loaded.source == "sourceA"
    repo2.close()


def test_queue_metrics(repo):
    # Seed various job states
    # Pending
    repo.publication_queue.add_job(
        PublicationJob("j1", "a1", "dest1", "pending", 10, "normal", "src1")
    )
    repo.publication_queue.add_job(
        PublicationJob("j2", "a2", "dest1", "pending", 10, "normal", "src1")
    )
    # Processing (under lease)
    repo.publication_queue.add_job(
        PublicationJob("j3", "a3", "dest1", "processing", 10, "normal", "src1")
    )
    # Succeeded
    repo.publication_queue.add_job(
        PublicationJob("j4", "a4", "dest1", "succeeded", 10, "normal", "src1")
    )
    # Dead letter
    repo.publication_queue.add_job(
        PublicationJob("j5", "a5", "dest1", "dead_letter", 10, "normal", "src1")
    )

    metrics = repo.publication_queue.get_metrics()
    assert metrics["pending"] == 2
    assert metrics["processing"] == 1
    assert metrics["dead_letter"] == 1
    assert metrics["published"] == 1
    # queue_depth is pending + retrying + processing
    assert metrics["queue_depth"] == 3


def test_stale_lease_recovery(repo):
    now = datetime.now(UTC)

    # Leased job in the past (expired)
    repo.publication_queue.add_job(
        PublicationJob(
            id="expired_job",
            article_id="a1",
            destination="pwa",
            status="processing",
            priority=10,
            priority_level="normal",
            source="src",
            attempts=1,
            lease_expires_at=now - timedelta(seconds=10),
        )
    )

    # Leased job in the future (not expired)
    repo.publication_queue.add_job(
        PublicationJob(
            id="active_job",
            article_id="a2",
            destination="pwa",
            status="processing",
            priority=10,
            priority_level="normal",
            source="src",
            attempts=1,
            lease_expires_at=now + timedelta(seconds=10),
        )
    )

    processor = PublicationQueueProcessor(repo, [])
    recovered = processor.recover_expired_leases(now)
    assert recovered == 1

    job1 = repo.publication_queue.get_job("expired_job")
    assert job1.status == "retrying"
    assert job1.lease_expires_at is None

    job2 = repo.publication_queue.get_job("active_job")
    assert job2.status == "processing"


def test_global_and_source_rate_limits(repo):
    now = datetime.now(UTC)

    # Global limit = 10, Source limit = 5
    # Create 6 articles for sourceA, 6 articles for sourceB (Total 12 articles)
    for i in range(1, 7):
        create_test_article(repo, f"a_A_{i}", "sourceA")
        repo.publication_queue.add_job(
            PublicationJob(f"a_A_{i}:pwa", f"a_A_{i}", "pwa", "pending", 10, "normal", "sourceA")
        )
    for i in range(1, 7):
        create_test_article(repo, f"a_B_{i}", "sourceB")
        repo.publication_queue.add_job(
            PublicationJob(f"a_B_{i}:pwa", f"a_B_{i}", "pwa", "pending", 10, "normal", "sourceB")
        )

    publisher = MockPublisher("pwa")
    processor = PublicationQueueProcessor(
        repo, [publisher], max_global_per_hour=10, max_source_per_hour=5
    )

    # First cycle
    processor.process_cycle(now)

    # 1. Total successes cannot exceed global limit (10)
    # 2. Source successes cannot exceed source limit (5 per source)
    # So we expect exactly 5 successes from sourceA and exactly 5 successes from sourceB.
    source_a_pubs = [a for a in publisher.published_articles if a.source == "sourceA"]
    source_b_pubs = [a for a in publisher.published_articles if a.source == "sourceB"]

    assert len(publisher.published_articles) == 10
    assert len(source_a_pubs) == 5
    assert len(source_b_pubs) == 5

    # Any subsequent cycle within the same hour window should not publish more because global limit is reached
    processor.process_cycle(now + timedelta(minutes=10))
    assert len(publisher.published_articles) == 10


def test_fair_scheduling_and_priority_ordering(repo):
    now = datetime.now(UTC)

    # Source A has a massive backlog of 15 normal items.
    for i in range(1, 16):
        create_test_article(repo, f"a_{i}", "sourceA")
        repo.publication_queue.add_job(
            PublicationJob(
                f"a_{i}:pwa",
                f"a_{i}",
                "pwa",
                "pending",
                10,
                "normal",
                "sourceA",
                created_at=now - timedelta(minutes=i),
            )
        )

    # Source B has 2 normal items.
    for i in range(1, 3):
        create_test_article(repo, f"b_{i}", "sourceB")
        repo.publication_queue.add_job(
            PublicationJob(
                f"b_{i}:pwa",
                f"b_{i}",
                "pwa",
                "pending",
                10,
                "normal",
                "sourceB",
                created_at=now - timedelta(minutes=i),
            )
        )

    # High priority items for Source C (breaking/urgent)
    create_test_article(repo, "c_high", "sourceC")
    repo.publication_queue.add_job(
        PublicationJob("c_high:pwa", "c_high", "pwa", "pending", 40, "breaking", "sourceC")
    )

    publisher = MockPublisher("pwa")
    # Let's say global limit is 4
    processor = PublicationQueueProcessor(
        repo, [publisher], max_global_per_hour=4, max_source_per_hour=5
    )

    processor.process_cycle(now)

    # Since priority is breaking first:
    # 1. c_high (breaking) MUST be published first!
    # Then we have 3 slots left.
    # 2. Due to fair scheduling, the remaining slots should be shared round-robin between sourceA and sourceB:
    #    We expect at least 1 from sourceB and 2 from sourceA (or vice versa), rather than all from sourceA's backlog!
    published_ids = [a.id for a in publisher.published_articles]

    assert "c_high" in published_ids
    assert len(published_ids) == 4

    # Check that sourceB was not starved by sourceA's backlog
    b_pubs = [id_ for id_ in published_ids if id_.startswith("b_")]
    a_pubs = [id_ for id_ in published_ids if id_.startswith("a_")]
    assert len(b_pubs) >= 1
    assert len(a_pubs) >= 1


def test_retry_backoff_and_dead_letter(repo):
    now = datetime.now(UTC)

    create_test_article(repo, "fail_art", "src")
    job = PublicationJob(
        id="fail_art:pwa",
        article_id="fail_art",
        destination="pwa",
        status="pending",
        priority=10,
        priority_level="normal",
        source="src",
        max_attempts=3,
    )
    repo.publication_queue.add_job(job)

    # Publisher always fails
    failing_publisher = MockPublisher("pwa", success=False)
    processor = PublicationQueueProcessor(repo, [failing_publisher], base_backoff_seconds=10.0)

    # Attempt 1
    processor.process_cycle(now)
    job = repo.publication_queue.get_job("fail_art:pwa")
    assert job.status == "retrying"
    assert job.attempts == 1
    assert job.next_attempt_at == now + timedelta(seconds=10)  # 10 * 2^0

    # Running process_cycle right away shouldn't retry because next_attempt_at is in the future
    processor.process_cycle(now + timedelta(seconds=5))
    job = repo.publication_queue.get_job("fail_art:pwa")
    assert job.attempts == 1

    # Attempt 2 (Advance time past backoff)
    processor.process_cycle(now + timedelta(seconds=11))
    job = repo.publication_queue.get_job("fail_art:pwa")
    assert job.status == "retrying"
    assert job.attempts == 2
    assert job.next_attempt_at == now + timedelta(seconds=11) + timedelta(seconds=20)  # 10 * 2^1

    # Attempt 3 (Advance past second backoff -> Exhausts attempts and goes to dead_letter)
    processor.process_cycle(now + timedelta(seconds=32))
    job = repo.publication_queue.get_job("fail_art:pwa")
    assert job.status == "dead_letter"
    assert job.attempts == 3


def test_concurrent_worker_safety(repo):
    now = datetime.now(UTC)
    create_test_article(repo, "a1", "src")
    job = PublicationJob("a1:pwa", "a1", "pwa", "pending", 10, "normal", "src")
    repo.publication_queue.add_job(job)

    publisher = MockPublisher("pwa")
    processor = PublicationQueueProcessor(repo, [publisher])

    # Simulate atomic lock by checking that once a job is in processing state,
    # another process_cycle call does not retrieve it or execute it again.
    # We will mark it as processing manually
    job.status = "processing"
    job.lease_expires_at = now + timedelta(seconds=30)
    repo.publication_queue.save_job(job)

    # Execute cycle
    processor.process_cycle(now)

    # The publisher should not have been called because the job was locked!
    assert len(publisher.published_articles) == 0
