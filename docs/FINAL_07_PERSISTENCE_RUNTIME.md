# FINAL-07 — Press Persistence / Reporting / Runtime Hardening

**Issue:** YasinPress-Rewrite- #115  
**Date:** 2026-08-16  
**Version:** 1.0.0

## Goal

Execute real remaining work from umbrella #96: persistence integrity, reporting, startup/recovery, runtime failure handling — without unrelated product changes.

## Audit results

| Area | Evidence | Gap fixed in this Issue? |
|------|----------|--------------------------|
| Persistence restart | `tests/test_persistence_restart.py` PASS | Already solid |
| Persistent runtime / queue | `test_persistent_runtime.py`, `test_persistent_publishing.py` PASS | Already solid |
| Operational / hourly reports | `test_operational_report*.py`, `test_hourly_report_*` PASS | Already solid |
| Recovery | `yasinpress/recovery.py` + scheduler watchdog | Already solid |
| Startup/shutdown | CLI/runtime tests present | Already solid |
| Eitaa RTL rendering | #93 contract: Persian text leads, emoji trails | **Stale test assertions** fixed |
| Yasin-AI optional path | Public contracts; tests pass when `yasinai` installed | Contract-safe |

## Fix applied

`tests/test_timestamp_integrity.py` expected **emoji-led** timestamp lines, which contradicts the post-#93 Eitaa RTL contract enforced in `yasinpress/publishing/eitaa.py` and `tests/test_eitaa_rendering.py`. Assertions updated to require trailing emoji:

- `زمان خبر: … 🕐`
- `آخرین به‌روزرسانی: … 🕐`
- `زمان انتشار: نامشخص 🕐`

## Disposition of #96

Umbrella **Phase 4: Persistence, Reporting and Runtime Hardening** is **SUBSUMED** by #115. No remaining concrete defect required a separate Issue after this reconciliation.

## Acceptance

| Criterion | Status |
|-----------|--------|
| Confirmed defects fixed with regression tests | Timestamp integrity aligned + eitaa rendering suite |
| Persistence/reporting deterministic | Existing suite green |
| Startup/shutdown/recovery tested | Existing suite green |
| Full Press test suite | **314 passed** |
| #96 closed via this Issue | Yes |
| Yasin-AI remains contract-safe | Public-only path unchanged |
