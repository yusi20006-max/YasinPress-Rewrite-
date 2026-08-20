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
- Yasin-AI contract tests isolated from the optional external runtime while still validating the versioned public contract boundary
- Eitaa regressions validate canonical rendering and breaking-news rules without false expectations
- FINAL-08 repository-side runtime certification merged through PR #133, covering Worker vs persistent publication queue separation, runtime tick dispatch, idempotency, freshness, and zero external I/O in the test path
- FINAL-09 release-gate consistency hardening merged through PR #135
- FINAL-10 CI/release command parity merged through PR #137
- HARDEN-12 standalone live Eitaa helper removed through PR #145

## Final certification

### Repository code gate

**GREEN** — repository-side code, tests, runtime-path certification, CI/release parity, and credential-free safety controls are complete on `main`.

The repository code gate is distinct from production certification. Passing repository checks does not claim that a live Termux/Eitaa production publication has been verified.

### Remaining operational gate

- Production smoke test and final certification in the target Termux environment.
- The production Eitaa smoke test requires configured runtime credentials supplied only through the environment and must not expose or commit secrets.
- Record the exact commit SHA, Python/Termux/Ruff versions, automated test count, and operational result before declaring `FINAL / GREEN`.

### Non-blocking administrative debt

- Issue #118: repository secret-scanning control remains an administrative GitHub setting and is explicitly non-blocking for application/release certification.

## Release gate

YasinPress repository code, architecture, CI contract, Termux bootstrap, repository-side runtime certification, release documentation, and credential-free test safety are GREEN. The only functional release blocker remaining is operational production certification in the target Termux/Eitaa environment.
