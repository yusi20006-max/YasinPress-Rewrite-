# YasinPress Release Readiness

## Status

**CI green — release candidate ready.**

## Verified gates

- Python 3.13 runtime gate: passed
- Test suite: passed
- Ruff lint gate: passed
- Scheduler/runtime contracts: passed
- Persistence and restart/idempotency tests: passed
- Pipeline/category/priority contracts: passed
- E2E publishing contracts: passed
- Packaging metadata: Python `>=3.13`

## Architecture boundary

YasinPress is an independent news ingestion, processing, persistence, scheduling, and publishing application. Its architecture must remain aligned with the canonical Yasin documentation without introducing undocumented cross-project dependencies.

## Current release decision

The repository is ready to move from CI stabilization into release preparation. Remaining work is release metadata and documentation synchronization rather than blocking implementation defects.

## Release checklist

- [x] CI green on `main`
- [x] Python 3.13 compatibility verified
- [x] Test suite green
- [x] Ruff gate green
- [ ] Create/tag the intended release version
- [ ] Publish release notes
- [ ] Synchronize YASIN-DOCS with the final architecture state

## Note

GitHub Actions currently reports a Node.js 20 deprecation warning for `actions/checkout@v4` and `actions/setup-python@v5`. This is infrastructure maintenance and is not a YasinPress release blocker.
