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

YasinPress independently owns news ingestion, processing, persistence, scheduling, and publishing. The canonical integration boundary is external orchestration through YasinHub/YasinCLI; YasinPress must not acquire undocumented direct dependencies on other Yasin projects.

## Current release decision

Implementation stabilization is complete. The remaining release work is metadata, release notes, and synchronization with YASIN-DOCS rather than blocking implementation defects.

## Release checklist

- [x] CI green on `main`
- [x] Python 3.13 compatibility verified
- [x] Test suite green
- [x] Ruff gate green
- [x] Release readiness recorded in-repository
- [ ] Create/tag the intended release version
- [ ] Publish release notes
- [ ] Synchronize YASIN-DOCS with the final architecture state

## Non-blocking infrastructure warning

GitHub Actions reports a Node.js 20 deprecation warning for `actions/checkout@v4` and `actions/setup-python@v5`. This is infrastructure maintenance and is not a YasinPress release blocker.
