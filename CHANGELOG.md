# Changelog

## 1.0.0 - 2026-07-15

- Initial production-ready YasinPress Rewrite release.
- Added clean architecture package layout, SQLite persistence, RSS ingestion, processing, AI abstraction, publishing, scheduling, caching, monitoring, API, CLI, configuration, plugins, security, performance utilities, tests, and documentation.
- Hardened persistent SQLite queue, Eitaa HTML rendering, multi-source fair scheduling rate limits, and watchdog recovery boundaries.
- Resolved module name-shadowing import conflicts by restructuring `scheduler` and `monitoring` into robust packages.
- Added JSON serialization of `source_metadata` dict field across all article repositories.
