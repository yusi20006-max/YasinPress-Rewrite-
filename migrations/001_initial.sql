CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    published_at TEXT NOT NULL,
    category TEXT
);
