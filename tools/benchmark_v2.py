"""Produce source-locked V1/V2 evidence through the Docker Compose harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc
SOURCE_PATHS = [
    "Dockerfile",
    "constraints.lock",
    "docker-compose.evidence.yml",
    "docker-compose.yml",
    "config/loki.yml",
    "config/otel-collector-evidence.yml",
    "config/otel-collector.yml",
    "config/tempo.yml",
    "prometheus.yml",
    "grafana/provisioning/datasources/signals.yml",
    "src/observability_stack/api.py",
    "src/observability_stack/application.py",
    "src/observability_stack/benchmark.py",
    "src/observability_stack/domain.py",
    "src/observability_stack/infrastructure/metrics.py",
    "src/observability_stack/infrastructure/telemetry.py",
]
LOCK_PATHS = ["pyproject.toml", "constraints.lock", "requirements.txt", "Dockerfile"]


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def combined_digest(root: Path, paths: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update((root / relative).read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def git_output(root: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()


def compose_command(*arguments: str) -> list[str]:
    return ["docker", "compose", "-f", "docker-compose.evidence.yml", *arguments]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="observability-stack:local")
    parser.add_argument(
        "--producer", choices=("local", "github-actions", "other-ci"), default="local"
    )
    parser.add_argument("--ci-run-url")
    parser.add_argument(
        "--output", default="benchmarks/publication/observability-stack-v2.json"
    )
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    if args.producer != "local" and not args.ci_run_url:
        raise SystemExit("--ci-run-url is required for a non-local producer")

    root = Path(__file__).resolve().parents[1]
    source_commit = git_output(root, "rev-parse", "HEAD")
    if git_output(root, "status", "--porcelain"):
        raise SystemExit("benchmark requires a clean tree before it starts")

    v1_path = root / "benchmarks/results/observability-stack-v1.json"
    v2_path = root / args.output
    v1_path.parent.mkdir(parents=True, exist_ok=True)
    v2_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(compose_command("down", "--volumes", "--remove-orphans"), cwd=root)
    if not args.skip_build:
        subprocess.run(compose_command("build", "app"), cwd=root, check=True)

    image_id = subprocess.check_output(
        ["docker", "image", "inspect", "--format", "{{.Id}}", args.image], text=True
    ).strip()
    if not image_id.startswith("sha256:"):
        raise SystemExit(f"unexpected Docker image id: {image_id}")

    started_at = datetime.now(UTC)
    started = time.perf_counter()
    try:
        subprocess.run(
            compose_command(
                "up",
                "--abort-on-container-exit",
                "--exit-code-from",
                "benchmark",
            ),
            cwd=root,
            check=True,
        )
        subprocess.run(
            compose_command(
                "cp",
                "benchmark:/output/observability-stack-v1.json",
                str(v1_path),
            ),
            cwd=root,
            check=True,
        )
    finally:
        subprocess.run(
            compose_command("down", "--volumes", "--remove-orphans"),
            cwd=root,
            check=False,
        )
    duration = time.perf_counter() - started
    if not v1_path.is_file():
        raise SystemExit("evidence Compose completed without producing the V1 result")
    result: dict[str, Any] = json.loads(v1_path.read_text(encoding="utf-8"))
    recovery = [float(value) for value in result["samples"]]
    detection = [
        float(value) for value in result["metrics"]["incident_detection_seconds"]
    ]
    correlation = [
        1.0 if all(run["signals"].values()) else 0.0 for run in result["runs"]
    ]
    config = {
        "runs": 3,
        "warmup": 1,
        "signals": ["metrics", "traces", "logs"],
        "detection_delay_seconds": 0.05,
        "recovery_delay_seconds": 0.05,
        "concurrency": 1,
    }
    publication: dict[str, Any] = {
        "schema_version": 2,
        "run_id": str(uuid.uuid4()),
        "project": "observability-stack",
        "benchmark_id": "correlated-incident-signals",
        "workload": {
            "version": "2.0.0",
            "fixture_digest": combined_digest(root, SOURCE_PATHS),
            "config_digest": sha256_bytes(
                json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
            ),
            "warmup_iterations": 1,
            "measured_iterations": 3,
            "concurrency": 1,
        },
        "metrics": [
            {
                "name": "incident_recovery_seconds",
                "value": statistics.median(recovery),
                "unit": "seconds",
                "direction": "lower_is_better",
                "samples": recovery,
                "failures": 0,
                "summary": {
                    "min": min(recovery),
                    "median": statistics.median(recovery),
                    "max": max(recovery),
                },
            },
            {
                "name": "incident_detection_seconds",
                "value": statistics.median(detection),
                "unit": "seconds",
                "direction": "lower_is_better",
                "samples": detection,
                "failures": 0,
                "summary": {"median": statistics.median(detection)},
            },
            {
                "name": "signal_correlation_rate",
                "value": statistics.mean(correlation),
                "unit": "ratio",
                "direction": "target",
                "samples": correlation,
                "failures": correlation.count(0.0),
                "summary": {"target": 1.0, "signals_per_run": 3},
            },
        ],
        "execution": {
            "command": (
                "docker compose -f docker-compose.evidence.yml up "
                "--abort-on-container-exit --exit-code-from benchmark"
            ),
            "started_at": started_at.isoformat().replace("+00:00", "Z"),
            "duration_seconds": round(duration, 6),
            "exit_code": 0,
            "repeat": 3,
        },
        "environment": {
            "runtime": "python-3.12.13",
            "architecture": platform.machine().lower(),
            "hardware_class": (
                "docker-local" if args.producer == "local" else "github-actions-ubuntu"
            ),
        },
        "provenance": {
            "source_commit": source_commit,
            "clean_tree": True,
            "image_ref": f"{args.image}@{image_id}",
            "image_digest": image_id,
            "dependency_lock_digest": combined_digest(root, LOCK_PATHS),
            "producer": args.producer,
            "artifact_digest": sha256_file(v1_path),
        },
        "comparability_key": (
            "correlated-incident-signals:2.0.0:runs-3:signals-3:"
            "delay-0.05-0.05:python-3.12.13"
        ),
    }
    if args.ci_run_url:
        publication["provenance"]["ci_run_url"] = args.ci_run_url
    v2_path.write_text(json.dumps(publication, indent=2) + "\n", encoding="utf-8")
    print(f"v1_result={v1_path}")
    print(f"v2_result={v2_path}")
    print(f"source_commit={source_commit}")
    print(f"image_digest={image_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
