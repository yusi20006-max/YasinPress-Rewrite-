import sqlite3

from yasinpress.database.repositories import ArticleRepository


def test_operational_reports_are_persisted_and_limited_to_latest_24():
    repo = ArticleRepository(sqlite3.connect(":memory:"))
    for index in range(30):
        repo.save_operational_report({"timestamp": f"2026-01-01T{index:02d}:00:00+00:00", "received": index})

    reports = list(repo.recent_operational_reports())
    assert len(reports) == 24
    assert reports[0]["received"] == 29
    assert reports[-1]["received"] == 6
