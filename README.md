# YasinPress Rewrite

YasinPress Rewrite is a production-oriented Python 3.13+ news automation platform. It ingests RSS feeds, normalizes and enriches articles, persists state in SQLite, schedules resilient background work, publishes independently to web feeds and messaging channels, exposes an HTTP-style service layer, and ships with a command-line interface.

## Features

- Clean Architecture package layout with explicit domain boundaries.
- SQLite repositories, migrations, transactional unit of work, and backups.
- RSS fetching, source management, filtering, duplicate detection, validation, and formatting.
- AI provider abstraction for summaries, categorization, tagging, and title optimization.
- Independent PWA JSON Feed and RSS 2.0 publishing, with atomic file replacement and bounded feed history.
- Optional Eitaa publishing; web publishing does not depend on Eitaa being configured.
- Priority queue, retry policy, scheduler, cache, health checks, metrics, diagnostics, and statistics.
- Configuration from defaults, JSON, YAML, and environment variables.
- Plugin loader, security helpers, concurrency utilities, REST-style router, and CLI.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
yasinpress status
yasinpress health
yasinpress config
yasinpress run
```

When `YASINPRESS_FEEDS` is configured, `yasinpress run` fetches the feeds on the scheduler interval and processes new articles. PWA and RSS publishers are active independently and write to:

- `data/pwa/feed.json` — JSON Feed 1.1 for the PWA/web layer.
- `data/rss/feed.xml` — RSS 2.0 for standard feed readers.

The output paths, titles, feed URLs, maximum item count, scheduling, freshness, and publication limits are configurable through `.env` using the variables documented in `.env.example`.

Eitaa credentials are optional. If they are absent, PWA and RSS publishing continue normally.

## Project tree

```text
yasinpress/        Application package
docs/              Architecture, API, and developer documentation
tests/             Unit and integration tests
migrations/        SQL migrations
scripts/           Operational scripts
data/              Runtime-generated PWA/RSS feed files
```

## License

Released under the MIT License.
