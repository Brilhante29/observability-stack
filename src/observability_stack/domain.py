"""Framework-free failure scenario and incident state transitions."""

from __future__ import annotations

from dataclasses import dataclass, replace


class ControlledFailure(RuntimeError):
    """Raised when the demo failure is intentionally enabled."""

    def __init__(self, incident_id: str, reason: str) -> None:
        super().__init__(reason)
        self.incident_id = incident_id
        self.reason = reason


@dataclass(frozen=True)
class Incident:
    """Immutable state for one controlled incident."""

    incident_id: str
    reason: str
    opened_at: float
    detected_at: float | None = None
    recovered_at: float | None = None

    def __post_init__(self) -> None:
        if not self.incident_id.strip():
            raise ValueError("incident_id must not be blank")
        if not self.reason.strip():
            raise ValueError("reason must not be blank")
        if self.detected_at is not None and self.detected_at < self.opened_at:
            raise ValueError("detected_at must not precede opened_at")
        if self.recovered_at is not None and self.recovered_at < self.opened_at:
            raise ValueError("recovered_at must not precede opened_at")

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
        if now < self.opened_at:
            raise ValueError("detection time must not precede opened_at")
        return replace(self, detected_at=now)

    def recover(self, now: float) -> "Incident":
        if not self.active:
            return self
        if now < self.opened_at:
            raise ValueError("recovery time must not precede opened_at")
        return replace(self, recovered_at=now)
