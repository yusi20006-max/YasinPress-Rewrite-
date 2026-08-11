# YasinPress Runtime Contract

Status: Production architecture contract

## Scheduler

The scheduler is responsible only for triggering work on a reliable cadence. It must not contain article/business logic.

Required scheduled jobs:

- RSS polling
- queue dispatch
- source health/recovery checks
- hourly report generation
- metrics aggregation/retention
- stale lock recovery

Jobs must be idempotent or protected by a durable lock/lease so overlapping scheduler ticks cannot duplicate work.

## Watchdog

The watchdog supervises long-running components and records heartbeats. It must detect:

- scheduler stopped
- worker stopped
- queue stalled
- database unavailable
- publisher repeatedly failing
- source manager unavailable

Watchdog actions are bounded and safe: record failure, attempt controlled recovery, and avoid restart loops.

## Recovery

Recovery order:

1. detect and record failure
2. release/recover stale work leases
3. restart the affected worker/component
4. verify health
5. resume pending work
6. escalate to critical state after repeated unsuccessful recovery

Pending queue jobs must survive process restarts. A job already acknowledged as published must not be published again during recovery.

## Process lifecycle

```text
start
  -> initialize config
  -> initialize database
  -> validate dependencies
  -> load queue
  -> start scheduler
  -> start workers
  -> start watchdog
  -> healthy
```

Shutdown is graceful: stop accepting new work, finish/lease current safe operations, persist state, and close resources.

## Operational defaults

- normal article freshness: 12 hours
- global publication target: 10 messages/hour
- per-source target: 5 messages/hour
- hourly operational report: once per hour, 24 reports/day
- retry/backoff: bounded and persistent

All values must remain configuration-driven rather than hardcoded in worker logic.

## Failure isolation

An unavailable RSS source, AI provider, or Eitaa publisher must not terminate the complete application. Components report health independently and the system continues where safe.

## Observability

Every component exposes a health state and heartbeat. Logs should identify component, operation, result, duration, and error class without leaking secrets or full article payloads.
