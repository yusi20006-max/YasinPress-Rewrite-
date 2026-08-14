"""Database migrations for durable article state."""

import sqlite3  # noqa: I001


_ARTICLE_COLUMNS = (
    "event_id",
    "received_at",
    "lifecycle_state",
    "ai_state",
    "ai_error",
    "source_metadata",
    "updated_at",
    "fetched_at",
    "processed_at",
    "published_to_channel_at",
)

_INITIAL_ARTICLES_SCHEMA = """CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    published_at TEXT,
    category TEXT,
    event_id TEXT,
    received_at TEXT,
    lifecycle_state TEXT,
    ai_state TEXT,
    ai_error TEXT,
    source_metadata TEXT,
    updated_at TEXT,
    fetched_at TEXT,
    processed_at TEXT,
    published_to_channel_at TEXT
)"""

_SAVEPOINT = "yasinpress_articles_schema"


def _quote_identifier(value: str) -> str:
    """Quote a SQLite identifier safely."""
    return '"' + value.replace('"', '""') + '"'


def _published_at_is_not_null(connection: sqlite3.Connection) -> bool:
    """Return whether the current articles schema still requires published_at."""
    rows = connection.execute("PRAGMA table_info(articles)").fetchall()
    for row in rows:
        name = row[1] if not isinstance(row, sqlite3.Row) else row["name"]
        notnull = row[3] if not isinstance(row, sqlite3.Row) else row["notnull"]
        if name == "published_at":
            return bool(notnull)
    return False


def _make_published_at_nullable(create_sql: str) -> str:
    """Remove only the legacy NOT NULL constraint from published_at."""
    lowered = create_sql.lower()
    published_index = lowered.find("published_at")
    if published_index < 0:
        raise RuntimeError("published_at column is missing from legacy schema")

    boundaries = [
        index
        for index in (lowered.find(",", published_index), lowered.find(")", published_index))
        if index >= 0
    ]
    if not boundaries:
        raise RuntimeError("Unable to locate published_at column boundary")

    column_end = min(boundaries)
    not_null_index = lowered.rfind("not null", published_index, column_end)
    if not_null_index < 0:
        raise RuntimeError("Unable to locate published_at NOT NULL constraint")

    constraint_end = not_null_index + len("not null")
    return create_sql[:not_null_index].rstrip() + create_sql[constraint_end:]


def _rename_articles_create_statement(create_sql: str) -> str:
    """Change the legacy articles table name in its CREATE TABLE statement."""
    lowered = create_sql.lower()
    create_index = lowered.find("create table")
    if create_index < 0:
        raise RuntimeError("Unable to locate CREATE TABLE statement")

    cursor = create_index + len("create table")
    while cursor < len(create_sql) and create_sql[cursor].isspace():
        cursor += 1

    if lowered.startswith("if not exists", cursor):
        cursor += len("if not exists")
        while cursor < len(create_sql) and create_sql[cursor].isspace():
            cursor += 1

    identifiers = (
        ('"articles"', len('"articles"')),
        ("[articles]", len("[articles]")),
        ("`articles`", len("`articles`")),
        ("articles", len("articles")),
    )
    for identifier, length in identifiers:
        if lowered.startswith(identifier, cursor):
            return create_sql[:cursor] + "articles__migration" + create_sql[cursor + length :]

    raise RuntimeError("Unable to locate articles table name")


def _rebuild_articles_table(connection: sqlite3.Connection) -> None:
    """Rebuild a legacy articles table while preserving its schema objects."""
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='articles'"
    ).fetchone()
    if not row or not row[0]:
        raise RuntimeError("articles table definition is unavailable")

    create_sql = _make_published_at_nullable(str(row[0]))
    replacement_sql = _rename_articles_create_statement(create_sql)

    preserved_objects = connection.execute(
        """
        SELECT type, sql
        FROM sqlite_master
        WHERE tbl_name = 'articles'
          AND type IN ('index', 'trigger')
          AND sql IS NOT NULL
        ORDER BY CASE type WHEN 'index' THEN 0 ELSE 1 END, name
        """
    ).fetchall()

    columns = connection.execute("PRAGMA table_info(articles)").fetchall()
    column_names = [
        row[1] if not isinstance(row, sqlite3.Row) else row["name"]
        for row in columns
    ]
    quoted_columns = ", ".join(_quote_identifier(name) for name in column_names)

    connection.execute("DROP TABLE IF EXISTS articles__migration")
    connection.execute(replacement_sql)
    connection.execute(
        f"INSERT INTO articles__migration ({quoted_columns}) "
        f"SELECT {quoted_columns} FROM articles"
    )
    connection.execute("DROP TABLE articles")
    connection.execute("ALTER TABLE articles__migration RENAME TO articles")

    for object_row in preserved_objects:
        connection.execute(object_row[1])


def migrate(connection: sqlite3.Connection) -> None:
    """Apply the article schema migrations atomically and idempotently."""
    connection.execute(f"SAVEPOINT {_SAVEPOINT}")
    try:
        connection.execute(_INITIAL_ARTICLES_SCHEMA)

        existing_columns = {
            row[1] if not isinstance(row, sqlite3.Row) else row["name"]
            for row in connection.execute("PRAGMA table_info(articles)").fetchall()
        }
        for column in _ARTICLE_COLUMNS:
            if column not in existing_columns:
                connection.execute(
                    f"ALTER TABLE articles ADD COLUMN {_quote_identifier(column)} TEXT"
                )

        if _published_at_is_not_null(connection):
            _rebuild_articles_table(connection)

        connection.execute(f"RELEASE SAVEPOINT {_SAVEPOINT}")
    except Exception:
        connection.execute(f"ROLLBACK TO SAVEPOINT {_SAVEPOINT}")
        connection.execute(f"RELEASE SAVEPOINT {_SAVEPOINT}")
        raise


MIGRATIONS: tuple[str, ...] = (
    _INITIAL_ARTICLES_SCHEMA,
)
