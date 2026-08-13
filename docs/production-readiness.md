# YasinPress Production Readiness

Status: Release gate

## Verified architecture

- Feed items are deduplicated before pipeline processing.
- Articles persist through the shared SQLite repository.
- Jobs persist through the shared SQLite repository.
- Publishing uses retry-aware `ReliablePublisher`.
- Successful destination publishes are protected by idempotency keys.
- Delivery history and idempotency state share the application's SQLite connection.
- Runtime startup performs database readiness checks and interrupted-job recovery.
- CLI exposes configuration, health, and runtime startup contracts.

## Functional gates

- [ ] Multi-source RSS ingestion
- [ ] Source health isolation/recovery
- [ ] 12-hour freshness enforcement for all articles, including breaking news
- [ ] Breaking/urgent classification without a freshness exemption
- [ ] Cross-source deduplication
- [ ] Event/update grouping
- [ ] Immutable News ID
- [ ] Persistent article state
- [ ] Persistent publication queue
- [ ] Fair multi-source scheduling
- [ ] Global 10/hour publication cap
- [ ] Per-source 5/hour target
- [ ] Retry and dead-letter handling
- [ ] AI rewrite/classification/fallback
- [ ] AI marker in public output
- [ ] Linked source-name output with no raw URL
- [ ] Eitaa failure isolation
- [ ] Hourly report generation
- [ ] PWA API contract
- [ ] PWA dashboard
- [ ] Scheduler/watchdog/recovery

## Reliability gates

- restart during RSS fetch
- restart during queue processing
- publisher failure and recovery
- AI provider timeout/failure
- database lock/error
- internet outage and recovery
- malformed RSS
- duplicate article across multiple sources
- stale article rejection
- new update to an old event
- full hourly quota
- queue backlog recovery

## Security gates

- secrets only from secure configuration/environment
- no tokens in logs
- authenticated admin API
- safe input validation
- no arbitrary URL fetching beyond configured source policy
- dependency audit

## Performance gates

- RSS sources fetched independently
- queue operations remain bounded under backlog
- PWA pagination required for large collections
- metrics/report generation must not block publishing workers

## Critical integration path

```text
Feed -> Dedup -> Pipeline -> AI -> Article SQLite -> Publisher -> Retry -> Delivery History + Idempotency
```

## Release process

1. Run unit and integration tests.
2. Run end-to-end pipeline with mock publisher.
3. Run Eitaa integration test with production-like configuration without exposing credentials.
4. Verify hourly rate-limit accounting.
5. Verify 24-hour report retention/view.
6. Verify restart/recovery scenarios.
7. Merge implementation PRs only after their tests pass.
8. Tag a production release.

The GitHub connector cannot execute the complete local test suite; CI/local execution remains a release gate. A legacy `yasinpress/publishing/base.py` protocol may still require normalization if it conflicts with the canonical publishing export.
