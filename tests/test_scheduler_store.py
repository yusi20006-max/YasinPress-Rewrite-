from yasinpress.scheduler.jobs import new_job
from yasinpress.scheduler.store import InMemoryJobStore


def test_job_store_round_trip():
    store = InMemoryJobStore()
    job = new_job("feed-fetch")
    store.save(job)
    assert store.get(job.id) is job
    assert store.all() == (job,)
