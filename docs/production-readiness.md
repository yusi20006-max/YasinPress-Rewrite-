# YasinPress Production Readiness

## Verified architecture

- Feed items are deduplicated before pipeline processing.
- Articles persist through the shared SQLite repository.
- Jobs persist through the shared SQLite repository.
- Publishing uses retry-aware `ReliablePublisher`.
- Successful destination publishes are protected by idempotency keys.
- Delivery history and idempotency state share the application's SQLite connection.
- Runtime startup performs database readiness checks and interrupted-job recovery.
- CLI exposes configuration, health, and runtime startup contracts.

## Critical integration path

```text
Feed -> Dedup -> Pipeline -> AI -> Article SQLite -> Publisher -> Retry -> Delivery History + Idempotency
```

## Remaining verification

The repository connector does not execute the complete test suite. The integration tests added for publishing, persistence/restart, scheduler resilience, recovery, and feed-to-publish behavior should be executed in CI before release.

One legacy `yasinpress/publishing/base.py` file still contains an older publisher protocol. The canonical contract is exported by `yasinpress/publishing/__init__.py`; the GitHub contents API currently returns a 409 when attempting to replace/delete the stale file, so this file should be normalized in the next local/CI-capable pass.
