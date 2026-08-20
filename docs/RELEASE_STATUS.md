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
- POST-RELEASE-05 CI automation hardening merged through PR #154
- POST-RELEASE-06 credential-safe production certification preflight and evidence schema merged through PR #156
- HARDEN-13 repository secret-exposure regression gate merged through PR #158

## Final certification

### Repository code gate

**GREEN** — repository-side code, tests, runtime-path certification, CI/release parity, credential-free safety controls, and the supplementary repository secret-exposure gate are complete on `main`.

The repository code gate is distinct from production certification. Passing repository checks does not claim that a live Termux/Eitaa production publication has been verified.

### Remaining operational gate

Use `docs/PRODUCTION_CERTIFICATION_EVIDENCE.md` and run:

```sh
python scripts/production_certification_preflight.py --json
```

The preflight is read-only and reports credential configuration by presence only. It does not publish externally.

Then perform the manual production gate in the target Termux environment. Before declaring `FINAL / GREEN`, record the following non-secret evidence:

- repository commit SHA
- YasinPress package version
- Python version
- Termux/platform information
- Ruff version
- Hermes service state
- Yasin-AI service state
- YasinPress service state
- YasinRelay service state
- protected credential configuration status only
- automated repository test count and release-gate result
- manual Eitaa smoke-test result
- manual production AI-provider result
- final operator timestamp

The production Eitaa smoke test requires configured runtime credentials supplied only through the environment. Credential values must never be exposed in logs, issue comments, PRs, screenshots, or repository files.

### Certification boundary

`FINAL / GREEN` is reserved for the state where both repository-code certification and the manual operational production gate have been recorded successfully. Repository CI must remain credential-free and external-publisher-free even after operational certification is completed.

### Non-blocking administrative debt

- Issue #118: repository secret-scanning control remains an administrative GitHub setting and is explicitly non-blocking for application/release certification. The repository now also has the supplementary local secret-exposure regression gate from HARDEN-13 / PR #158.

## Release gate

YasinPress repository code, architecture, CI contract, Termux bootstrap, repository-side runtime certification, release documentation, credential-free test safety, and repository secret-exposure regression checks are GREEN. The remaining functional release blocker is operational production certification in the target Termux/Eitaa environment.
