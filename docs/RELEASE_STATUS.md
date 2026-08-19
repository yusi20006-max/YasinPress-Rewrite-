# YasinPress Release Status

**Version:** 1.0.0

**Decision:** READY — finalization in progress

## Completed

- Canonical architecture and YASIN-DOCS boundary
- Persistence and publishing hardening
- Retry/recovery and idempotency coverage
- CLI and package regression gates
- CI contract and release documentation gates
- Static security and placeholder scans
- GitHub Actions CI passed on main commit a3c08d22cd (2026-08-13): YasinPress CI ✅, Python Compatibility ✅, Actions Probe ✅
- 237 unit and integration tests passed on Python 3.13
- Ruff checks passed with zero errors
- Issue #121: Persian Eitaa title normalization and canonical message-format regression coverage merged in PR #123 (commit `2f2f2c9ec6282361ce43192d4af9fd46900f1f23`)

## Current finalization gate

### Completed

- Persian title normalization at the Eitaa publishing boundary
- Bidi-safe Persian-leading logical blocks
- Removal of known title metadata decorations
- Exact regression coverage for reported titles and normal/breaking output

### Remaining

- Finalization Phase 2 — Termux bootstrap, production smoke test, and final certification (Issue #124; PR #120 is the existing implementation candidate)
- P2 repository secret scanning control (Issue #118)

## Release gate

The application architecture and runtime gates remain **READY**. Final certification remains blocked only by the explicitly listed finalization tasks above.
