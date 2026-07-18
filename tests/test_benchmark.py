import unittest

from observability_stack.benchmark import run_benchmark


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_is_deterministic_and_has_evidence_fields(self) -> None:
        result = run_benchmark(repetitions=3)
        self.assertEqual(result["metric"], "simulated_mttr_minutes")
        self.assertEqual(result["value"], 1.2)
        self.assertEqual(result["samples"], [1.2, 1.2, 1.2])
        self.assertIn("method", result)
        self.assertIn("image", result)
        self.assertIn("metrics", result)
