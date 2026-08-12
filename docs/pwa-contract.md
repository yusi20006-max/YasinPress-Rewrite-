# YasinPress PWA Contract

Status: Production architecture contract

## Boundary

The PWA is an independent client. It communicates through the HTTP/API service boundary and must not access SQLite, repositories, or internal Python modules directly.

## Dashboard sections

1. Overview
2. Sources
3. Articles
4. Queue
5. Publishing
6. Hourly Reports
7. System Health
8. Settings (authenticated)

## Overview

Show:

- service status
- uptime
- current queue depth
- hourly published count / 10
- received and processed counts
- AI status
- Eitaa status
- internet status
- active/degraded source count
- latest hourly report

## Sources

Show each source's name, URL, enabled state, health state, last success/failure, response time, recent article count, and consecutive errors.

## Articles

Support pagination and filtering by source, category, priority, breaking flag, AI state, freshness, and lifecycle state. Display `news_id` and `event_id` where available.

## Queue

Show pending, processing, retrying, failed, and dead-letter jobs with priority, source, News ID, attempts, scheduled time, and last error. Retry/cancel actions are authenticated administrative operations.

## Publishing

Show global hourly usage, recent successful/failed deliveries, and publisher health. Never display credentials.

## Hourly reports

Show the 24 daily reports with received, accepted, rejected, duplicate, expired, AI, queued, published, failed, source health, queue, internet, and publisher state.

## UX requirements

- Mobile-first; Termux/Android operation is a primary use case.
- Read-only dashboards remain usable during partial source failures.
- Loading/error/empty states are explicit.
- Data refresh should not reset filters unnecessarily.
- Use mock API data during independent PWA development, preserving the real API field names.
