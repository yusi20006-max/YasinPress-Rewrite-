# YasinPress Release Status

**Version:** 1.0.0

**Decision:** FINALIZATION — operational certification in progress

## Completed

- Canonical architecture and YASIN-DOCS boundary
- Persistence and publishing hardening
- Retry/recovery and idempotency coverage
- CLI and package regression gates
- CI contract and release documentation gates
- Static security and placeholder scans
- Termux bootstrap PR #120 merged successfully as commit `fffa57f3be7ae820f652c6be02b5891cdf0f91df`
- Issue #121: Persian Eitaa title normalization and canonical message-format regression coverage merged in PR #123 / commit `2f2f2c9ec6282361ce43192d4af9fd46900f1f23`
- Termux bootstrap CI on PR #120: YasinPress CI, Python Compatibility, Phase 6 Python Compatibility Matrix, and Actions Probe all succeeded

## Current finalization gate

### Completed

- Persian title normalization at the Eitaa publishing boundary
- Bidi-safe Persian-leading logical blocks
- Removal of known title metadata decorations
- Exact regression coverage for reported titles and normal/breaking output
- Termux-native Ruff bootstrap; PyPI Ruff source build removed from the Termux path

### Remaining

- Production smoke test and final certification (Issue #125)
- P2 repository secret scanning control (Issue #118)

## Release gate

The application architecture, CI gates, and Termux bootstrap are GREEN. Final release certification remains blocked only by the production smoke test and the explicitly non-blocking Issue #118 security-control debt.
