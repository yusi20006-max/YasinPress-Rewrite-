# YasinPress Production Test Plan

Status: Production readiness contract

## Functional pipeline

1. Fetch multiple RSS sources concurrently.
2. Normalize articles and assign immutable News IDs.
3. Reject normal articles older than 12 hours.
4. Preserve explicit Breaking/urgent exception behavior.
5. Deduplicate repeated articles across fetch cycles and sources.
6. Persist queue state and recover it after restart.
7. Enforce maximum 10 publications/hour and source fairness.
8. Retry transient Eitaa failures without duplicate publication.
9. Mark AI-rewritten messages with `🤖`.
10. Render source name as the article link without exposing raw URL.

## Resilience tests

- one RSS source unavailable;
- all RSS sources temporarily unavailable;
- internet outage during fetch;
- AI provider timeout/rate limit;
- Eitaa timeout/rate limit;
- database restart/failure;
- worker crash during processing;
- process restart with jobs in `processing`;
- scheduler restart during hourly report;
- watchdog recovery;
- repeated publisher failure leading to dead letter.

## Data integrity

- News ID remains stable across restart/retry.
- Published article is never republished because of a transient worker crash.
- Event ID groups related reports without merging distinct updates.
- Hourly report is idempotent.
- Queue leases expire safely.
- Secrets never appear in logs, reports, API responses, or persisted article content.

## Rate/fairness tests

Use deterministic fixtures with at least four active sources. Verify:

- no more than 10 successful publications in any configured hour window;
- no single source exceeds its configured per-source cap;
- eligible high-priority items are selected first;
- normal sources continue receiving capacity when another source has a large backlog;
- retries do not bypass the global limiter.

## PWA/API tests

- dashboard loads with mock data;
- dashboard loads with real API data;
- pagination/filtering preserve contract semantics;
- partial source failure does not blank the whole dashboard;
- authentication protects administrative mutations;
- credentials are never returned.

## Release gate

Production release requires all existing tests plus the critical pipeline, persistence, rate-limit, duplicate-prevention, recovery, publisher, and API contract tests to pass.
