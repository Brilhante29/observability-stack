"""In-memory adapter used by the default local runtime."""

from __future__ import annotations

from threading import Lock

from ..domain import Incident


class InMemoryIncidentStore:
    """Thread-safe enough for the single-process demo and its tests."""

    def __init__(self) -> None:
        self._incident: Incident | None = None
        self._lock = Lock()

    def get(self) -> Incident | None:
        with self._lock:
            return self._incident

    def put(self, incident: Incident) -> None:
        with self._lock:
            self._incident = incident
