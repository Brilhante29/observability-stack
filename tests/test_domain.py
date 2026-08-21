import unittest

from observability_stack.application import ObservationService
from observability_stack.domain import ControlledFailure, Incident
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
        self.service.start_failure("incident-001", "database_timeout")
        with self.assertRaises(ControlledFailure) as failure:
            self.service.checkout()
        self.assertEqual(failure.exception.incident_id, "incident-001")
        self.clock.advance(72)
        incident = self.service.recover_failure()
        self.assertIsNotNone(incident)
        self.assertEqual(self.service.checkout()["status"], "ok")

    def test_detection_and_recovery_are_measured_from_incident_open(self) -> None:
        self.service.start_failure("incident-002", "dependency_timeout")
        self.clock.advance(24)
        incident = self.service.detect_failure()
        self.assertEqual(incident.detection_seconds, 24)
        self.clock.advance(48)
        incident = self.service.recover_failure()
        self.assertEqual(incident.recovery_seconds, 72)

    def test_time_cannot_move_before_incident_open(self) -> None:
        self.clock.value = 10
        self.service.start_failure("incident-003", "dependency_timeout")
        self.clock.value = 9
        with self.assertRaisesRegex(ValueError, "must not precede"):
            self.service.detect_failure()

    def test_empty_store_has_no_incident_to_detect_or_recover(self) -> None:
        self.assertIsNone(self.service.detect_failure())
        self.assertIsNone(self.service.recover_failure())
        self.assertEqual(self.service.status(), {"active": False, "incident": None})

    def test_incident_rejects_invalid_identity_reason_and_timestamps(self) -> None:
        with self.assertRaisesRegex(ValueError, "incident_id"):
            Incident("", "timeout", 1)
        with self.assertRaisesRegex(ValueError, "reason"):
            Incident("incident-004", "", 1)
        with self.assertRaisesRegex(ValueError, "detected_at"):
            Incident("incident-004", "timeout", 2, detected_at=1)
        with self.assertRaisesRegex(ValueError, "recovered_at"):
            Incident("incident-004", "timeout", 2, recovered_at=1)

    def test_transitions_are_idempotent_and_validate_time(self) -> None:
        incident = Incident("incident-005", "timeout", 10)
        with self.assertRaisesRegex(ValueError, "detection time"):
            incident.detect(9)
        with self.assertRaisesRegex(ValueError, "recovery time"):
            incident.recover(9)
        detected = incident.detect(11)
        self.assertIs(detected.detect(12), detected)
        recovered = detected.recover(13)
        self.assertIs(recovered.recover(14), recovered)
