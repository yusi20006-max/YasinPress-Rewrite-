# YasinPress Rewrite

YasinPress Rewrite is a production-oriented Python 3.13 news automation platform. It ingests RSS feeds, normalizes and enriches articles, persists state in SQLite, schedules resilient background work, publishes to messaging channels and webhooks, exposes an HTTP-style service layer, and ships with a command-line interface.

## Features

- Clean Architecture package layout with explicit domain boundaries.
- SQLite repositories, migrations, transactional unit of work, and backups.
- RSS fetching, source management, filtering, duplicate detection, validation, and formatting.
- AI provider abstraction for summaries, categorization, tagging, and title optimization.
- Publisher abstraction for Telegram, Eitaa, and generic webhooks.
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
pytest
```

## Project tree

```text
yasinpress/        Application package
docs/              Architecture, API, and developer documentation
tests/             Unit and integration tests
migrations/        SQL migrations
scripts/           Operational scripts
```

## License

Released under the MIT License.
