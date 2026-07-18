"""Use cases for the observable checkout demo."""

from __future__ import annotations

from .domain import ControlledFailure, Incident
from .ports import Clock, IncidentStore


class ObservationService:
    """Coordinates incident policy through a narrow storage port."""

    def __init__(self, store: IncidentStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    def start_failure(self, reason: str) -> Incident:
        incident = Incident(reason=reason, opened_at=self._clock())
        self._store.put(incident)
        return incident

    def detect_failure(self) -> Incident | None:
        incident = self._store.get()
        if incident is None:
            return None
        detected = incident.detect(self._clock())
        self._store.put(detected)
        return detected

    def recover_failure(self) -> Incident | None:
        incident = self._store.get()
        if incident is None:
            return None
        recovered = incident.recover(self._clock())
        self._store.put(recovered)
        return recovered

    def checkout(self) -> dict[str, str]:
        incident = self._store.get()
        if incident is not None and incident.active:
            raise ControlledFailure(incident.reason)
        return {"status": "ok", "service": "checkout"}

    def status(self) -> dict[str, object]:
        incident = self._store.get()
        if incident is None:
            return {"active": False, "incident": None}
        return {
            "active": incident.active,
            "incident": {
                "reason": incident.reason,
                "opened_at": incident.opened_at,
                "detected_at": incident.detected_at,
                "recovered_at": incident.recovered_at,
                "detection_seconds": incident.detection_seconds,
                "recovery_seconds": incident.recovery_seconds,
            },
        }
