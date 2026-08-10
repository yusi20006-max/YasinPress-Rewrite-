from datetime import UTC, datetime

from yasinpress.scheduler.jobs import JobStatus
from yasinpress.scheduler.store import InMemoryJobStore
from yasinpress.scheduler.tasks import build_pipeline_job, execute_job
from yasinpress.sources.feed import FeedItem


def test_pipeline_job_executes_and_persists_result():
    captured = []
    items = [FeedItem("News", "https://example.com/1", "Body", datetime.now(UTC))]
    job, handler = build_pipeline_job("test", items, captured.append)
    result = execute_job(job, handler, InMemoryJobStore())
    assert result.status == JobStatus.SUCCEEDED
    assert captured[0].processed == 1
