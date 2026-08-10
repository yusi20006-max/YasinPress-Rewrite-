import sqlite3

from yasinpress.health import check_database


def test_database_health():
    conn = sqlite3.connect(":memory:")
    result = check_database(conn)
    assert result.ok
    assert result.database
