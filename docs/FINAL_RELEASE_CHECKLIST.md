# YasinPress Final Release Checklist

## Code

- [x] Canonical publishing contract
- [x] Legacy publishing compatibility
- [x] Persistent publishing state
- [x] Idempotency
- [x] Retry/recovery coverage
- [x] E2E publishing coverage
- [x] Release metadata regression coverage

## CI

- [x] GitHub Actions workflow exists
- [x] Python 3.13 is tested
- [x] Source compilation is tested
- [x] Full pytest suite is invoked
- [ ] Current `main` commit has a visible successful workflow run

## Release

- [x] Version metadata is pinned at 1.0.0
- [x] Python production requirement is >=3.13
- [x] Release candidate documentation exists
- [x] Release gate documentation exists
- [x] CI compatibility documentation exists
- [x] Changelog exists
- [ ] Final release is marked READY

**Release decision:** NOT READY until the current `main` CI run is verified green.
