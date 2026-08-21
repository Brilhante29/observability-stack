"""Validate source-locked observability publication evidence."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from benchmark_v2 import LOCK_PATHS, SOURCE_PATHS
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "benchmarks/results/observability-stack-v1.json"
V2_PATH = ROOT / "benchmarks/publication/observability-stack-v2.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def git_blob(commit: str, path: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
        capture_output=True,
        check=False,
    )
    require(completed.returncode == 0, f"source commit lacks {path}")
    return completed.stdout


def combined_source_digest(commit: str, paths: list[str]) -> str:
    value = hashlib.sha256()
    for path in paths:
        value.update(path.encode("utf-8"))
        value.update(b"\0")
        value.update(git_blob(commit, path))
        value.update(b"\0")
    return "sha256:" + value.hexdigest()


def metric_map(v2: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {metric["name"]: metric for metric in v2["metrics"]}


def main() -> None:
    manifest = (ROOT / "project.yaml").read_text(encoding="utf-8")
    if re.search(r"(?m)^status:\s*published\s*$", manifest) is None:
        print("publication_evidence=not-applicable")
        return

    require(V1_PATH.is_file(), "published project requires V1 evidence")
    require(V2_PATH.is_file(), "published project requires V2 evidence")
    v1: dict[str, Any] = json.loads(V1_PATH.read_text(encoding="utf-8"))
    v2: dict[str, Any] = json.loads(V2_PATH.read_text(encoding="utf-8"))
    schema = json.loads(
        (ROOT / ".portfolio/contracts/benchmark-result-v2.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(v2)
    require(v2["project"] == "observability-stack", "unexpected V2 project")
    require(v2["execution"]["repeat"] == 3, "publication requires three runs")
    metrics = metric_map(v2)
    require(
        metrics["incident_recovery_seconds"]["samples"] == v1["samples"],
        "V1/V2 recovery samples mismatch",
    )
    require(
        metrics["incident_detection_seconds"]["samples"]
        == v1["metrics"]["incident_detection_seconds"],
        "V1/V2 detection samples mismatch",
    )
    require(
        metrics["signal_correlation_rate"]["value"] == 1.0,
        "signal correlation must be complete",
    )
    require(
        all(metric["failures"] == 0 for metric in metrics.values()),
        "V2 contains failures",
    )
    require(
        all(all(run["signals"].values()) for run in v1["runs"]),
        "V1 contains an uncorrelated run",
    )

    commit = v2["provenance"]["source_commit"]
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "invalid source commit")
    require(
        v2["workload"]["fixture_digest"] == combined_source_digest(commit, SOURCE_PATHS),
        "source fixture digest mismatch",
    )
    require(
        v2["provenance"]["dependency_lock_digest"]
        == combined_source_digest(commit, LOCK_PATHS),
        "dependency lock digest mismatch",
    )
    require(
        v2["provenance"]["artifact_digest"] == digest(V1_PATH.read_bytes()),
        "V1 artifact digest mismatch",
    )
    for field in ("image_digest", "artifact_digest", "dependency_lock_digest"):
        require(
            re.fullmatch(r"sha256:[0-9a-f]{64}", v2["provenance"][field]) is not None,
            f"invalid {field}",
        )
    require(
        v2["provenance"]["image_ref"].endswith(v2["provenance"]["image_digest"]),
        "image reference and digest disagree",
    )
    serialized = json.dumps({"v1": v1, "v2": v2})
    for forbidden in ("C:\\Users\\", "github" + "_pat_", "gh" + "p_"):
        require(forbidden not in serialized, f"forbidden evidence value: {forbidden}")
    print("publication_evidence=passed")


if __name__ == "__main__":
    main()
