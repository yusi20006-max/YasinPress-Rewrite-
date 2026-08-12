"""Bounded heartbeat supervision for long-running YasinPress components."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Callable

class HealthState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"

@dataclass
class Heartbeat:
    name: str
    last_seen: datetime
    state: HealthState = HealthState.HEALTHY
    recovery_attempts: int = 0
    last_error: str | None = None
    def touch(self, when: datetime, *, reset_recovery: bool = False) -> None:
        self.last_seen = when
        self.state = HealthState.HEALTHY
        self.last_error = None
        if reset_recovery: self.recovery_attempts = 0

@dataclass(frozen=True)
class WatchdogPolicy:
    stale_after: timedelta = timedelta(minutes=2)
    max_recovery_attempts: int = 3
    recovery_cooldown: timedelta = timedelta(minutes=5)

class Watchdog:
    """Supervise heartbeats and invoke bounded recovery callbacks."""
    def __init__(self, *, now: Callable[[], datetime] | None = None, policy: WatchdogPolicy | None = None) -> None:
        self.now = now or (lambda: datetime.now(UTC))
        self.policy = policy or WatchdogPolicy()
        self.heartbeats: dict[str, Heartbeat] = {}
        self._last_recovery: dict[str, datetime] = {}
    def register(self, name: str) -> None:
        if not name: raise ValueError("component name must not be empty")
        self.heartbeats[name] = Heartbeat(name=name, last_seen=self.now())
    def touch(self, name: str) -> None:
        heartbeat = self.heartbeats.get(name)
        if heartbeat is None:
            self.register(name); heartbeat = self.heartbeats[name]
        heartbeat.touch(self.now())
    def inspect(self, recover: Callable[[str], bool] | None = None) -> tuple[Heartbeat, ...]:
        current = self.now()
        for heartbeat in self.heartbeats.values():
            if current - heartbeat.last_seen <= self.policy.stale_after: continue
            heartbeat.state = HealthState.DEGRADED
            if recover is None: continue
            if heartbeat.recovery_attempts >= self.policy.max_recovery_attempts:
                heartbeat.state = HealthState.FAILED; continue
            previous = self._last_recovery.get(heartbeat.name)
            if previous is not None and current - previous < self.policy.recovery_cooldown: continue
            self._last_recovery[heartbeat.name] = current
            heartbeat.recovery_attempts += 1
            try: recovered = bool(recover(heartbeat.name))
            except Exception as exc:
                heartbeat.last_error = exc.__class__.__name__; recovered = False
            if recovered:
                heartbeat.touch(current, reset_recovery=True); self._last_recovery.pop(heartbeat.name, None)
            elif heartbeat.recovery_attempts >= self.policy.max_recovery_attempts:
                heartbeat.state = HealthState.FAILED
        return tuple(self.heartbeats.values())
