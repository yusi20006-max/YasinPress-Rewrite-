import threading
import time
from datetime import UTC, datetime, timedelta

from yasinpress.database.models import Article, PublicationJob
from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing import PublishResult
from yasinpress.publishing.queue import QueueConfig, SQLitePublicationQueueEngine
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
                time.sleep(0.001)
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
    unique_articles = {art_id for art_id, _ in shared_published}
    assert len(unique_articles) <= 30


def test_concurrent_workers_respect_source_unique_article_cap(tmp_path):
    db_file = str(tmp_path / "test_source_cap.db")
    init_repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)
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
    unique_articles = {art_id for art_id, _ in shared_published}
    assert len(unique_articles) <= 5


def test_concurrent_workers_preserve_destination_fanout(tmp_path):
    db_file = str(tmp_path / "test_fanout.db")
    init_repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)
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
    assert len(shared_published) == 15
    unique_combinations = set(shared_published)
    assert len(unique_combinations) == 15


def test_expired_lease_is_recoverable(tmp_path):
    db_file = str(tmp_path / "test_lease_recovery.db")
    init_repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)
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
    assert sum(recovered_counts) == 10


def test_concurrent_processing_preserves_idempotency(tmp_path):
    db_file = str(tmp_path / "test_idempotency_concurrency.db")
    init_repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)
    create_article_and_job(init_repo, "art_1", "src", "pwa")
    init_repo.close()

    repo = SQLiteRepositories(db_file)
    repo.idempotency.mark("art_1:pwa")

    shared_published = []
    publisher = ConcurrentMockPublisher("pwa", shared_published)
    processor = PublicationQueueProcessor(repo, [publisher])
    processor.process_cycle(now)
    repo.close()

    assert len(shared_published) == 0


def test_queue_engine_global_limit_counts_unique_articles_across_destinations(tmp_path):
    db_file = str(tmp_path / "test_engine_unique_global_limit.db")
    repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)

    for article_id in ("art_1", "art_2", "art_3"):
        for destination in ("eitaa", "pwa", "rss"):
            create_article_and_job(repo, article_id, f"source_{article_id}", destination)

    engine = SQLitePublicationQueueEngine(
        repo.connection,
        QueueConfig(global_limit=2, source_limit=10),
    )

    claimed = []
    for _ in range(10):
        job = engine.claim_next(now)
        if job is None:
            break
        claimed.append(job)

    assert len(claimed) == 6
    assert {job.article_id for job in claimed} == {"art_1", "art_2"}
    assert {job.destination for job in claimed if job.article_id == "art_1"} == {"eitaa", "pwa", "rss"}
    assert {job.destination for job in claimed if job.article_id == "art_2"} == {"eitaa", "pwa", "rss"}
    repo.close()


def test_queue_engine_source_limit_counts_unique_articles_across_destinations(tmp_path):
    db_file = str(tmp_path / "test_engine_unique_source_limit.db")
    repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)

    for article_id in ("art_1", "art_2"):
        for destination in ("eitaa", "pwa", "rss"):
            create_article_and_job(repo, article_id, "same_source", destination)

    engine = SQLitePublicationQueueEngine(
        repo.connection,
        QueueConfig(global_limit=10, source_limit=1),
    )

    claimed = []
    for _ in range(10):
        job = engine.claim_next(now)
        if job is None:
            break
        claimed.append(job)

    assert len(claimed) == 3
    assert {job.article_id for job in claimed} == {"art_1"}
    assert {job.destination for job in claimed} == {"eitaa", "pwa", "rss"}
    repo.close()


def test_queue_engine_metrics_count_unique_articles(tmp_path):
    db_file = str(tmp_path / "test_engine_unique_metrics.db")
    repo = SQLiteRepositories(db_file)
    now = datetime.now(UTC)

    for destination in ("eitaa", "pwa"):
        create_article_and_job(repo, "art_1", "source", destination)
    engine = SQLitePublicationQueueEngine(repo.connection, QueueConfig(global_limit=5, source_limit=5))

    for destination in ("eitaa", "pwa"):
        job = engine.claim_next(now)
        assert job is not None
        assert job.destination == destination
        engine.mark_success(job.id, now=now)

    metrics = engine.metrics(now)
    assert metrics["published_last_hour"] == 1
    assert metrics["remaining_global_capacity"] == 4
    repo.close()
