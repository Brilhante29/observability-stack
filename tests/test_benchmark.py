import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from observability_stack.api import create_app
from observability_stack.benchmark import FileSignalProbe, run_benchmark


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_drives_http_and_requires_three_signals(self) -> None:
        with TestClient(create_app(otlp_endpoint="")) as client:
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "result.json"
                result = run_benchmark(
                    repetitions=3,
                    output=output,
                    client=client,
                    detection_delay_seconds=0,
                    recovery_delay_seconds=0,
                )
                self.assertTrue(output.exists())
        self.assertEqual(result["metric"], "incident_recovery_seconds")
        self.assertEqual(len(result["samples"]), 3)
        self.assertEqual(result["summary"]["signal_correlation_rate"], 1.0)
        self.assertTrue(all(run["signals"]["metrics"] for run in result["runs"]))

    def test_file_probe_requires_incident_and_every_trace_in_both_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            traces = root / "traces.json"
            logs = root / "logs.json"
            evidence = "incident-123 trace-a trace-b"
            traces.write_text(evidence, encoding="utf-8")
            logs.write_text(evidence, encoding="utf-8")
            result = FileSignalProbe(traces, logs, timeout_seconds=0.1).verify(
                "incident-123", {"trace-a", "trace-b"}
            )
        self.assertEqual(result, {"traces": True, "logs": True})

    def test_file_probe_reports_missing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = FileSignalProbe(
                root / "missing-traces.json",
                root / "missing-logs.json",
                timeout_seconds=0.01,
            ).verify("incident-404", {"trace-404"})
        self.assertEqual(result, {"traces": False, "logs": False})

    def test_repetitions_must_be_positive(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            run_benchmark(repetitions=0)
