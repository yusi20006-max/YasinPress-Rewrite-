from datetime import UTC, datetime, timedelta

from yasinpress.scheduler.watchdog import HealthState, Watchdog, WatchdogPolicy


def test_watchdog_marks_stale_component_and_recovers() -> None:
    current = datetime(2026, 8, 12, 10, 0, tzinfo=UTC)
    watchdog = Watchdog(
        now=lambda: current,
        policy=WatchdogPolicy(stale_after=timedelta(seconds=30)),
    )
    watchdog.register("queue")
    current += timedelta(minutes=1)

    recovered: list[str] = []
    result = watchdog.inspect(lambda name: recovered.append(name) or True)

    assert recovered == ["queue"]
    assert result[0].state == HealthState.HEALTHY
    assert result[0].recovery_attempts == 1


def test_watchdog_prevents_unbounded_recovery_loop() -> None:
    current = datetime(2026, 8, 12, 10, 0, tzinfo=UTC)
    watchdog = Watchdog(
        now=lambda: current,
        policy=WatchdogPolicy(
            stale_after=timedelta(seconds=30),
            max_recovery_attempts=2,
            recovery_cooldown=timedelta(0),
        ),
    )
    watchdog.register("publisher")
    current += timedelta(minutes=1)

    assert watchdog.inspect(lambda _: False)[0].state == HealthState.DEGRADED
    assert watchdog.inspect(lambda _: False)[0].state == HealthState.FAILED
    assert watchdog.heartbeats["publisher"].recovery_attempts == 2
