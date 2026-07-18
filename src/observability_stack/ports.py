"""Small application ports used to keep policy independent from adapters."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from .domain import Incident


class IncidentStore(Protocol):
    def get(self) -> Incident | None:
        """Return the current incident, if one has been opened."""

    def put(self, incident: Incident) -> None:
        """Persist the current incident."""


Clock = Callable[[], float]
