# Changelog

## Unreleased - Finalization

- Fixed YasinPress Eitaa title rendering to reuse the canonical headline normalization pipeline.
- Normalized known feed metadata decorations while preserving meaningful Persian punctuation and orthography.
- Preserved bidi-safe Persian-leading message blocks and kept invisible bidi controls out of serialized Eitaa HTML.
- Added exact regression coverage for the three reported Persian titles, normal/breaking layouts, HTML escaping, metadata noise, and AI marker behavior.
- Merged as PR #123 / commit `2f2f2c9ec6282361ce43192d4af9fd46900f1f23`, closing Issue #121.

## 1.0.0 - 2026-07-15

- Initial production-ready YasinPress Rewrite release.
- Added clean architecture package layout, SQLite persistence, RSS ingestion, processing, AI abstraction, publishing, scheduling, caching, monitoring, API, CLI, configuration, plugins, security, performance utilities, tests, and documentation.
- Hardened persistent SQLite queue, Eitaa HTML rendering, multi-source fair scheduling rate limits, and watchdog recovery boundaries.
- Resolved module name-shadowing import conflicts by restructuring `scheduler` and `monitoring` into robust packages.
- Added JSON serialization of `source_metadata` dict field across all article repositories.
