from yasinpress.ai.categorizer import Categorizer
from yasinpress.api.app import ApiApp
from yasinpress.api.routes import health_route
from yasinpress.cache.manager import CacheManager
from yasinpress.scheduler.queue import JobQueue
from yasinpress.scheduler.scheduler import Scheduler
from yasinpress.scheduler.worker import Worker


def test_cache_manager() -> None:
    cache = CacheManager()
    assert cache.remember("k", lambda: "v") == "v"
    assert cache.remember("k", lambda: "x") == "v"


def test_api_health() -> None:
    app = ApiApp(); app.route("/health", health_route)
    assert app.handle("/health").status_code == 200


def test_scheduler_worker() -> None:
    values: list[str] = []
    queue = JobQueue(); Scheduler(queue).schedule("append", lambda: values.append("done"), priority=1)
    Worker(queue).run_once()
    assert values == ["done"]


def test_categorizer() -> None:
    assert Categorizer().categorize("market news") == "economy"
