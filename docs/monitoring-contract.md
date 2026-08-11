# YasinPress Monitoring Contract

Status: Production architecture contract

## Purpose

Monitoring is operational state, not a second source of truth. The PWA and the hourly support report must consume the same persisted metrics/state.

## Hourly report

A report is generated at the start of every hour and covers the previous hour plus current system state.

Required fields:

- report timestamp and timezone
- received articles
- accepted articles
- rejected articles
- expired articles (>12h)
- duplicates
- AI rewritten
- AI fallback/original
- queued
- published
- failed
- retrying
- current queue depth
- active source count
- degraded/inactive source count
- source names with failures
- internet connectivity status
- AI provider status
- Eitaa publisher status
- scheduler status
- watchdog status
- process uptime

## Terminal observability

The runtime should remain quiet about individual article contents by default. It should expose useful progress instead:

```text
14:00 | RSS: +28 | Queue: 7 | Published: 3/10 | AI: 24 | Failed: 0
```

A new fetch cycle should report source-level counts, for example `28 news received from BBC Persian`, without dumping every article to the terminal.

## Alert thresholds

- source consecutive failures: warning/degraded
- publisher consecutive failures: warning
- queue growth without successful publication: warning
- database failure: critical
- scheduler/watchdog stopped: critical
- internet unavailable: degraded

## Privacy and security

Never include Eitaa tokens, AI API keys, Authorization headers, raw secrets, or sensitive request payloads in logs or hourly reports.
