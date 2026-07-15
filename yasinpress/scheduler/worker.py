"""Queue worker."""
from .queue import JobQueue
from .retry import RetryPolicy

class Worker:
    """Executes queued jobs."""
    def __init__(self, queue: JobQueue, retry: RetryPolicy | None = None) -> None:
        self.queue = queue; self.retry = retry or RetryPolicy()
    def run_once(self) -> None:
        """Run one queued job."""
        job = self.queue.get(); self.retry.run(job.task)
