# YasinPress Final Release Checklist

## Code

- [x] Canonical publishing contract
- [x] Legacy publishing compatibility
- [x] Persistent publishing state
- [x] Idempotency
- [x] Retry/recovery coverage
- [x] E2E publishing coverage
- [x] Runtime/package regression coverage
- [x] CLI smoke coverage
- [x] Dependency consistency coverage
- [x] Static placeholder/security scan

## CI

- [x] GitHub Actions workflow exists
- [x] Workflow is manually dispatchable
- [x] Python 3.13 is the authoritative release runtime
- [x] Source compilation is tested
- [x] Full pytest suite is invoked
- [x] Ruff is invoked
- [x] CI integrity is regression-tested
- [ ] Current `main` commit has a visible successful workflow run

## Release

- [x] Version metadata is pinned at 1.0.0
- [x] Python production requirement is >=3.13
- [x] Release candidate documentation exists
- [x] Quality gate documentation exists
- [x] CI compatibility documentation exists
- [x] YASIN-DOCS alignment is documented
- [x] Hardening summary exists
- [x] Release status is explicit
- [x] Changelog baseline exists
- [ ] Final release is marked READY

**Release decision:** NOT READY until a successful current-main CI run is independently observable.
