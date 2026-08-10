from datetime import datetime, timezone

from yasinpress.database.sqlite import SQLiteRepositories
from yasinpress.publishing.history import DeliveryRecord


def test_delivery_history_and_idempotency_survive_restart(tmp_path):
    path = str(tmp_path / "state.db")
    first = SQLiteRepositories(path)
    first.delivery_history.add(
        DeliveryRecord("article-1", "rss", True, 1, "external-1", None, datetime.now(timezone.utc))
    )
    first.idempotency.mark("article-1:rss")
    first.close()

    second = SQLiteRepositories(path)
    assert len(second.delivery_history.for_article("article-1")) == 1
    assert second.idempotency.seen("article-1:rss")
    second.close()
