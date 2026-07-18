"""Deterministic MTTR benchmark for the controlled incident scenario."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .application import ObservationService
from .infrastructure.store import InMemoryIncidentStore


@dataclass
class LogicalClock:
    value: float = 0.0

    def now(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def measure_once() -> dict[str, float]:
    clock = LogicalClock()
    service = ObservationService(InMemoryIncidentStore(), clock.now)

    service.start_failure("dependency_timeout")
    clock.advance(24.0)
    service.detect_failure()
    clock.advance(48.0)
    incident = service.recover_failure()
    assert incident is not None
    assert incident.detection_seconds is not None
    assert incident.recovery_seconds is not None
    return {
        "detection_seconds": incident.detection_seconds,
        "recovery_seconds": incident.recovery_seconds,
        "mttr_minutes": incident.recovery_seconds / 60.0,
    }


def run_benchmark(
    repetitions: int = 3,
    output: Path | None = None,
    command: str | None = None,
) -> dict[str, object]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    samples = [measure_once() for _ in range(repetitions)]
    mttr_samples = [sample["mttr_minutes"] for sample in samples]
    benchmark_command = (
        command
        or "python -m observability_stack.benchmark "
        "--output benchmarks/results/observability-stack-v1.json"
    )
    result: dict[str, object] = {
        "schema_version": "1.0",
        "project": "25-observability-stack",
        "metric": "simulated_mttr_minutes",
        "value": mttr_samples[0],
        "unit": "minutes",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "command": benchmark_command,
        "repeat": repetitions,
        "samples": mttr_samples,
        "summary": {
            "mean": sum(mttr_samples) / len(mttr_samples),
            "min": min(mttr_samples),
            "max": max(mttr_samples),
            "detection_seconds": samples[0]["detection_seconds"],
            "recovery_seconds": samples[0]["recovery_seconds"],
        },
        "method": (
            "Open incident at logical t=0s, detect at t=24s, recover at t=72s; "
            "repeat with a deterministic logical clock."
        ),
        "fixture": {
            "reason": "dependency_timeout",
            "seed": 42,
            "dataset": "single controlled incident",
        },
        "image": "observability-stack:local (python:3.12-slim)",
        "metrics": {
            "incident_open_to_detection_seconds": samples[0]["detection_seconds"],
            "incident_open_to_recovery_seconds": samples[0]["recovery_seconds"],
            "repetitions": repetitions,
        },
        "environment": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
            "runtime": "logical-clock simulation; host scheduling excluded",
        },
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()
    result = run_benchmark(args.repeat, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
