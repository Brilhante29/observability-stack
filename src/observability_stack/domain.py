"""Framework-free failure scenario and incident state transitions."""

from __future__ import annotations

from dataclasses import dataclass, replace


class ControlledFailure(RuntimeError):
    """Raised when the demo failure is intentionally enabled."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Incident:
    """Immutable state for one controlled incident."""

    reason: str
    opened_at: float
    detected_at: float | None = None
    recovered_at: float | None = None

    @property
    def active(self) -> bool:
        return self.recovered_at is None

    @property
    def detection_seconds(self) -> float | None:
        if self.detected_at is None:
            return None
        return self.detected_at - self.opened_at

    @property
    def recovery_seconds(self) -> float | None:
        if self.recovered_at is None:
            return None
        return self.recovered_at - self.opened_at

    def detect(self, now: float) -> "Incident":
        if not self.active or self.detected_at is not None:
            return self
        return replace(self, detected_at=now)

    def recover(self, now: float) -> "Incident":
        if not self.active:
            return self
        return replace(self, recovered_at=now)
