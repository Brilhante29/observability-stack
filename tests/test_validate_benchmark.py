import unittest

from tools.validate_benchmark import validate


class BenchmarkContractTests(unittest.TestCase):
    def test_valid_three_signal_result_passes(self) -> None:
        run = {
            "signals": {"metrics": True, "traces": True, "logs": True},
            "trace_ids": ["a" * 32, "b" * 32, "c" * 32],
        }
        payload = {
            "metric": "incident_recovery_seconds",
            "unit": "seconds",
            "repeat": 3,
            "summary": {"signal_correlation_rate": 1.0},
            "runs": [run, run, run],
        }
        self.assertEqual(validate(payload), [])

    def test_missing_signal_fails_closed(self) -> None:
        payload = {
            "metric": "wrong",
            "unit": "minutes",
            "repeat": 1,
            "summary": {"signal_correlation_rate": 0.5},
            "runs": [{}],
        }
        errors = validate(payload)
        self.assertGreaterEqual(len(errors), 5)
