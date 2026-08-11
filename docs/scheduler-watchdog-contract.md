# YasinPress Scheduler, Watchdog and Recovery Contract

Status: Production architecture contract

## Runtime model

YasinPress is a long-running service. Scheduling, fetching, processing, publishing, reporting, and recovery are separate concerns and must not be coupled to a single infinite loop.

```text
Scheduler
  ├── RSS fetch cycle
  ├── queue worker cycle
  └── hourly report cycle

Watchdog
  ├── observes heartbeats
  ├── detects stalled workers
  └── triggers bounded recovery

Persistence
  └── survives process restart
```

## Scheduler

The scheduler must:

- run RSS ingestion at a configurable interval;
- wake queue workers when pending jobs exist;
- emit exactly one hourly report per hour with idempotency protection;
- avoid overlapping executions of the same job;
- tolerate temporary internet/source failures;
- shut down gracefully and release worker leases.

The scheduler must use timezone-aware timestamps and a monotonic clock for durations where appropriate.

## Watchdog

Every long-running worker exposes a heartbeat/last-progress timestamp. The watchdog checks:

- main process heartbeat;
- RSS worker heartbeat;
- queue worker heartbeat;
- hourly report heartbeat;
- API health;
- database availability.

A stalled worker is first marked degraded, then recovered using the least destructive action available. Recovery must be bounded and rate-limited to prevent restart loops.

## Recovery order

```text
stalled operation
    ↓
cancel/release expired lease
    ↓
restart worker task
    ↓
reconnect/reinitialize dependency
    ↓
full process restart only when necessary
```

## Restart safety

On startup the service must reconcile persisted state:

- recover jobs left in `processing` with expired leases;
- preserve `published` records and never republish them as new jobs;
- preserve News IDs;
- resume pending/retrying jobs;
- restore source health state safely;
- regenerate transient heartbeats rather than trusting stale runtime state.

## Hourly report idempotency

A report key is derived from the hour bucket. The system must not publish the same hourly support report twice after a scheduler restart or watchdog recovery.

## Failure policy

A failure in one component must not terminate unrelated components. Fatal startup failure is limited to required infrastructure such as an unavailable database when no recovery path exists.

## Observability

Recovery actions must be visible in structured operational logs and hourly metrics without exposing secrets. Include component, action, reason, attempt count, and outcome.

## Shutdown

Graceful shutdown must stop new work, allow safe in-flight completion up to a configured deadline, persist queue state, release leases, and terminate workers cleanly.
