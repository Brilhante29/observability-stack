"""Fail closed when observability benchmark evidence is incomplete."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("metric") != "incident_recovery_seconds":
        errors.append("metric must be incident_recovery_seconds")
    if payload.get("unit") != "seconds":
        errors.append("unit must be seconds")
    if payload.get("repeat") != 3:
        errors.append("repeat must be exactly 3")
    summary = payload.get("summary", {})
    if not isinstance(summary, dict) or summary.get("signal_correlation_rate") != 1.0:
        errors.append("signal_correlation_rate must be 1.0")
    runs = payload.get("runs", [])
    if not isinstance(runs, list) or len(runs) != 3:
        errors.append("runs must contain exactly 3 measurements")
        return errors
    for index, run in enumerate(runs):
        if not isinstance(run, dict):
            errors.append(f"run {index} must be an object")
            continue
        signals = run.get("signals")
        if signals != {"metrics": True, "traces": True, "logs": True}:
            errors.append(f"run {index} does not prove all three signals")
        trace_ids = run.get("trace_ids")
        if not isinstance(trace_ids, list) or len(trace_ids) != 3:
            errors.append(f"run {index} must contain three lifecycle trace IDs")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.result.read_text(encoding="utf-8"))
    errors = validate(payload)
    if errors:
        raise SystemExit("\n".join(f"- {error}" for error in errors))
    print("observability benchmark evidence passed")


if __name__ == "__main__":
    main()
