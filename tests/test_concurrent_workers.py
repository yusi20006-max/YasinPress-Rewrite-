import threading
import time
import sqlite3
from datetime import UTC, datetime, timedelta
import pytest

from yasinpress.database.models import Article, PublicationJob
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.queue import SQLitePublicationQueueEngine, QueueConfig
from yasinpress.publishing.queue_processor import PublicationQueueProcessor


class ConcurrentMockPublisher:
    def __init__(self, name: str, shared_list: list, delay: float = 0.0) -> None:
        self._name = name
        self.shared_list = shared_list
        self.delay = delay
        self.lock = threading.Lock()
        self.publish_count = 0

    @property
    def name(self) -> str:
        return self._name

    def publish(self, article) -> PublishResult:
        if self.delay > 0:
            time.sleep(self.delay)
        with self.lock:
            self.shared_list.append((article.id, self.name))
            self.publish_count += 1
        return PublishResult(True, self.name, external_id=article.id)


def create_article_and_job(repo: SQLiteRepositories, id_: str, source: str, destination: str, priority: int = 10) -> None:
    art = Article(
        id=id_, title="Test Article", url=f"https://example.com/{source}/{id_}",
        content="Some content", source=source, published_at=datetime.now(UTC),
    )
    repo.articles.save(art)
    repo.publication_queue.add_job(
        PublicationJob(
            id=f"{id_}:{destination}",
            article_id=id_,
            destination=destination,
            status="pending",
            priority=priority,
            priority_level="normal",
            source=source,
        )
    )


def test_atomic_claim_prevents_duplicate_claim(tmp_path):
    db_file = str(tmp_path / "test_duplicate_claims.db")
    init_repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)
    for i in range(50):
        create_article_and_job(init_repo, f"art_{i}", "src", "pwa")
    init_repo.close()

    claimed_jobs = []
    claimed_lock = threading.Lock()
    errors = []

    def worker_func():
        try:
            repo = SQLiteRepositories(db_file)
            engine = SQLitePublicationQueueEngine(repo.connection, QueueConfig(global_limit=100, source_limit=100))
            while True:
                job = engine.claim_next(now)
                if job is None:
                    break
                with claimed_lock:
                    claimed_jobs.append(job.id)
                time.sleep(0.001)  # tiny yield
            repo.close()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker_func) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Encountered worker errors: {errors}"
    assert len(claimed_jobs) == 50
    assert len(set(claimed_jobs)) == 50


def test_concurrent_workers_respect_global_unique_article_cap(tmp_path):
    db_file = str(tmp_path / "test_global_cap.db")
    init_repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)
    # 40 articles, each with unique source to avoid source limits
    for i in range(40):
        create_article_and_job(init_repo, f"art_{i}", f"src_{i}", "pwa")
    init_repo.close()

    shared_published = []
    errors = []

    def worker_func():
        try:
            repo = SQLiteRepositories(db_file)
            publisher = ConcurrentMockPublisher("pwa", shared_published, delay=0.01)
            processor = PublicationQueueProcessor(repo, [publisher], max_global_per_hour=30, max_source_per_hour=5)
            processor.process_cycle(now)
            repo.close()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker_func) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Encountered worker errors: {errors}"
    unique_articles = set(art_id for art_id, _ in shared_published)
    assert len(unique_articles) <= 30


def test_concurrent_workers_respect_source_unique_article_cap(tmp_path):
    db_file = str(tmp_path / "test_source_cap.db")
    init_repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)
    # 15 articles from the same source
    for i in range(15):
        create_article_and_job(init_repo, f"art_{i}", "same_source", "pwa")
    init_repo.close()

    shared_published = []
    errors = []

    def worker_func():
        try:
            repo = SQLiteRepositories(db_file)
            publisher = ConcurrentMockPublisher("pwa", shared_published, delay=0.01)
            processor = PublicationQueueProcessor(repo, [publisher], max_global_per_hour=30, max_source_per_hour=5)
            processor.process_cycle(now)
            repo.close()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker_func) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Encountered worker errors: {errors}"
    unique_articles = set(art_id for art_id, _ in shared_published)
    assert len(unique_articles) <= 5


def test_concurrent_workers_preserve_destination_fanout(tmp_path):
    db_file = str(tmp_path / "test_fanout.db")
    init_repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)
    # 5 articles, each with separate jobs for eitaa, pwa, and rss
    for i in range(5):
        for dest in ("eitaa", "pwa", "rss"):
            create_article_and_job(init_repo, f"art_{i}", "src", dest)
    init_repo.close()

    shared_published = []
    errors = []

    def worker_func():
        try:
            repo = SQLiteRepositories(db_file)
            publishers = [
                ConcurrentMockPublisher("eitaa", shared_published),
                ConcurrentMockPublisher("pwa", shared_published),
                ConcurrentMockPublisher("rss", shared_published),
            ]
            processor = PublicationQueueProcessor(repo, publishers, max_global_per_hour=30, max_source_per_hour=5)
            processor.process_cycle(now)
            repo.close()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker_func) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Encountered worker errors: {errors}"
    # There are 15 distinct job targets (5 articles * 3 destinations)
    # Fan-out should be preserved: all of them should be published
    assert len(shared_published) == 15
    unique_combinations = set(shared_published)
    assert len(unique_combinations) == 15


def test_expired_lease_is_recoverable(tmp_path):
    db_file = str(tmp_path / "test_lease_recovery.db")
    init_repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)
    # Enqueue 10 processing jobs with expired leases
    for i in range(10):
        init_repo.articles.save(Article(id=f"art_{i}", title="test", url=f"https://example.com/art_{i}", content="c", source="s"))
        init_repo.publication_queue.add_job(
            PublicationJob(
                id=f"art_{i}:pwa",
                article_id=f"art_{i}",
                destination="pwa",
                status="processing",
                priority=10,
                priority_level="normal",
                source="s",
                attempts=1,
                lease_expires_at=now - timedelta(seconds=10),
            )
        )
    init_repo.close()

    recovered_counts = []
    errors = []

    def worker_func():
        try:
            repo = SQLiteRepositories(db_file)
            processor = PublicationQueueProcessor(repo, [])
            count = processor.recover_expired_leases(now)
            recovered_counts.append(count)
            repo.close()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker_func) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Encountered worker errors: {errors}"
    # The sum of recovered jobs across all threads must be exactly 10!
    assert sum(recovered_counts) == 10


def test_concurrent_processing_preserves_idempotency(tmp_path):
    db_file = str(tmp_path / "test_idempotency_concurrency.db")
    init_repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)
    create_article_and_job(init_repo, "art_1", "src", "pwa")
    init_repo.close()

    # Pre-mark the idempotency key as seen
    repo = SQLiteRepositories(db_file)
    repo.idempotency.mark("art_1:pwa")

    shared_published = []
    publisher = ConcurrentMockPublisher("pwa", shared_published)
    processor = PublicationQueueProcessor(repo, [publisher])
    processor.process_cycle(now)
    repo.close()

    # Since the key was already marked, publish should not have been called!
    assert len(shared_published) == 0
