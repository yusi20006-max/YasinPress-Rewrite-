# Phase 2 — Relay-Parity Processing and Freshness Audit

Issue: #94

Implemented:
- enforce the 12-hour freshness gate before AI enrichment
- reject timestamp-unknown articles before AI and publication work
- preserve fetched/received/processed lifecycle metadata through enrichment
- preserve update timestamps and allow fresh updated articles to be reprocessed
- add regression coverage for stale, unknown-timestamp, updated, and metadata cases

CI: Python 3.13 release gate passed with tests and Ruff.
