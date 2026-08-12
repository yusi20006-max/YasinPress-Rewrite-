from yasinpress.scheduler.queue import Job, JobQueue
from yasinpress.scheduler.scheduler import Scheduler


def test_priority_queue_preserves_priority_order():
    queue = JobQueue()
    queue.put(Job(50, "normal", lambda: None))
    queue.put(Job(1, "breaking", lambda: None))
    queue.put(Job(10, "urgent", lambda: None))

    assert queue.get_nowait().name == "breaking"
    assert queue.get_nowait().name == "urgent"
    assert queue.get_nowait().name == "normal"


def test_scheduler_schedule_delegates_to_priority_queue():
    queue = JobQueue()
    scheduler = Scheduler(queue)
    scheduler.schedule("breaking", lambda: None, priority=1)
    assert queue.get_nowait().name == "breaking"
