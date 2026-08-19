# YasinPress Release Status

**Version:** 1.0.0

**Decision:** FINALIZATION — production certification pending

## Completed

- Canonical architecture and YASIN-DOCS boundary
- Persistence and publishing hardening
- Retry/recovery and idempotency coverage
- CLI and package regression gates
- CI contract and release documentation gates
- Static security and placeholder scans
- Termux bootstrap PR #120 merged successfully as commit `fffa57f3be7ae820f652c6be02b5891cdf0f91df`
- Issue #121: Persian Eitaa title normalization and canonical message-format regression coverage merged in PR #123 / commit `2f2f2c9ec6282361ce43192d4af9fd46900f1f23`
- Termux-native Ruff bootstrap; PyPI Ruff source build removed from the Termux path
- Final-gate regression correction PR #126 merged as commit `c3cc9d82bf20d7715ab224153409b7f0217956e5`
- Yasin-AI contract tests are isolated from the optional external runtime while still validating the versioned public contract boundary
- Eitaa regressions now validate the canonical rendering and breaking-news rules without false expectations
- Final repository-side runtime certification coverage added in Issue #132 / PR, including Worker vs persistent publication queue separation, runtime tick dispatch, idempotency, freshness, and zero external I/O test-path guarantees

## Final certification

### Code gate

**GREEN** — repository-side code, tests, and runtime-path certification are complete once the Issue #132 CI gate is green and merged.

The final production certification remains an operational gate in the target Termux environment. The production Eitaa smoke test requires configured runtime credentials and must be performed without exposing secrets.

### Remaining

- Production smoke test and final certification (operational verification)
- P2 repository secret scanning control (Issue #118, explicitly non-blocking)

## Release gate

YasinPress code, architecture, CI contract, Termux bootstrap, and repository-side runtime certification are GREEN. The only release blocker is operational production certification; Issue #118 remains non-blocking security-control debt.
