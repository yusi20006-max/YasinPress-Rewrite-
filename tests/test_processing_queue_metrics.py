from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.pipeline.service import ProcessingService


class FakeQueue:
    def __init__(self):
        self.jobs = {}

    def exists(self, job_id):
        return job_id in self.jobs

    def add_job(self, job):
        self.jobs[job.id] = job


class FakePublisher:
    name = "eitaa"

    def publish(self, article):
        raise AssertionError("queued processing must not publish directly")


def test_queue_mode_reports_destination_job_count(monkeypatch):
    queue = FakeQueue()
    service = ProcessingService(
        source="example.com",
        publishers=[FakePublisher()],
        publication_queue=queue,
    )
    item = type(
        "FeedItem",
        (),
        {
            "title": "خبر",
            "content": "متن",
            "url": "https://example.com/1",
            "published_at": datetime.now(UTC),
            "source": "example.com",
            "media_url": None,
            "media_type": None,
        },
    )()
    monkeypatch.setattr(service.pipeline, "process", lambda items: type("R", (), {"articles": [Article(id="a1", title="خبر", content="متن", url="https://example.com/1", source="example.com", published_at=datetime.now(UTC)),], "rejected": 0})())
    monkeypatch.setattr("yasinpress.pipeline.service.unique_items", lambda items: tuple(items))

    report = service.process([item])
    assert report.queued_count == 1
    assert len(queue.jobs) == 1
