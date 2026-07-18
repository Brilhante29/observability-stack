import unittest

from observability_stack.application import ObservationService
from observability_stack.domain import ControlledFailure
from observability_stack.infrastructure.store import InMemoryIncidentStore


class ManualClock:
    def __init__(self) -> None:
        self.value = 0.0

    def now(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class ObservationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = ManualClock()
        self.service = ObservationService(InMemoryIncidentStore(), self.clock.now)

    def test_checkout_fails_only_while_controlled_incident_is_active(self) -> None:
        self.assertEqual(self.service.checkout()["status"], "ok")
        self.service.start_failure("database_timeout")
        with self.assertRaises(ControlledFailure):
            self.service.checkout()
        self.clock.advance(72)
        incident = self.service.recover_failure()
        self.assertIsNotNone(incident)
        self.assertEqual(self.service.checkout()["status"], "ok")

    def test_detection_and_recovery_are_measured_from_incident_open(self) -> None:
        self.service.start_failure("dependency_timeout")
        self.clock.advance(24)
        incident = self.service.detect_failure()
        self.assertEqual(incident.detection_seconds, 24)
        self.clock.advance(48)
        incident = self.service.recover_failure()
        self.assertEqual(incident.recovery_seconds, 72)
