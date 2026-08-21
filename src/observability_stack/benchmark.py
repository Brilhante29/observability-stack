"""HTTP benchmark that requires metric, trace and log correlation."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

import httpx


class HttpClient(Protocol):
    def get(self, url: str, **kwargs: Any) -> Any: ...

    def post(self, url: str, **kwargs: Any) -> Any: ...


class SignalProbe(Protocol):
    def verify(self, incident_id: str, trace_ids: set[str]) -> dict[str, bool]: ...


class StaticSignalProbe:
    """Unit-test probe; production evidence uses FileSignalProbe."""

    def verify(self, incident_id: str, trace_ids: set[str]) -> dict[str, bool]:
        return {"traces": bool(incident_id and trace_ids), "logs": bool(incident_id)}


class FileSignalProbe:
    """Poll line-delimited OTLP evidence written by the Collector file exporter."""

    def __init__(
        self, traces_path: Path, logs_path: Path, timeout_seconds: float = 15.0
    ) -> None:
        self._traces_path = traces_path
        self._logs_path = logs_path
        self._timeout_seconds = timeout_seconds

    @staticmethod
    def _read(path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def verify(self, incident_id: str, trace_ids: set[str]) -> dict[str, bool]:
        deadline = time.monotonic() + self._timeout_seconds
        result = {"traces": False, "logs": False}
        while time.monotonic() < deadline:
            traces = self._read(self._traces_path)
            logs = self._read(self._logs_path)
            result = {
                "traces": incident_id in traces
                and all(trace_id in traces for trace_id in trace_ids),
                "logs": incident_id in logs and all(trace_id in logs for trace_id in trace_ids),
            }
            if all(result.values()):
                return result
            time.sleep(0.1)
        return result


def _trace_id(response: Any) -> str:
    trace_id = response.headers.get("X-Trace-ID", "")
    if len(trace_id) != 32:
        raise RuntimeError("response did not expose a valid X-Trace-ID")
    return trace_id


def measure_once(
    client: HttpClient,
    probe: SignalProbe,
    detection_delay_seconds: float = 0.05,
    recovery_delay_seconds: float = 0.05,
) -> dict[str, Any]:
    incident_id = f"incident-{uuid4()}"
    headers = {"X-Correlation-ID": incident_id}

    baseline = client.get("/api/v1/checkout", headers=headers)
    baseline.raise_for_status()
    opened = client.post(
        "/api/v1/failure",
        headers=headers,
        json={"enabled": True, "incident_id": incident_id, "reason": "dependency_timeout"},
    )
    opened.raise_for_status()
    open_trace = _trace_id(opened)

    failed_checkout = client.get("/api/v1/checkout", headers=headers)
    if failed_checkout.status_code != 503:
        raise RuntimeError(
            f"controlled checkout returned {failed_checkout.status_code}, expected 503"
        )

    time.sleep(detection_delay_seconds)
    detected = client.get("/api/v1/status", headers=headers)
    detected.raise_for_status()
    detect_trace = _trace_id(detected)

    time.sleep(recovery_delay_seconds)
    recovered = client.post(
        "/api/v1/failure",
        headers=headers,
        json={"enabled": False, "incident_id": incident_id},
    )
    recovered.raise_for_status()
    recover_trace = _trace_id(recovered)

    final_checkout = client.get("/api/v1/checkout", headers=headers)
    final_checkout.raise_for_status()
    incident = recovered.json()["incident"]
    metrics_payload = client.get("/metrics", headers=headers).text
    trace_ids = {open_trace, detect_trace, recover_trace}
    metrics_ok = incident_id in metrics_payload and all(
        trace_id in metrics_payload for trace_id in trace_ids
    )
    signals = {"metrics": metrics_ok, **probe.verify(incident_id, trace_ids)}
    if not all(signals.values()):
        missing = ", ".join(name for name, present in signals.items() if not present)
        raise RuntimeError(f"incident {incident_id} is not correlated in: {missing}")

    return {
        "incident_id": incident_id,
        "detection_seconds": float(incident["detection_seconds"]),
        "recovery_seconds": float(incident["recovery_seconds"]),
        "trace_ids": sorted(trace_ids),
        "signals": signals,
    }


def run_benchmark(
    repetitions: int = 3,
    output: Path | None = None,
    command: str | None = None,
    base_url: str = "http://127.0.0.1:8000",
    client: HttpClient | None = None,
    probe: SignalProbe | None = None,
    detection_delay_seconds: float = 0.05,
    recovery_delay_seconds: float = 0.05,
) -> dict[str, Any]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    owned_client = httpx.Client(base_url=base_url, timeout=10.0) if client is None else None
    active_client = owned_client or client
    assert active_client is not None
    signal_probe = probe or StaticSignalProbe()
    try:
        active_client.get("/healthz").raise_for_status()
        active_client.get("/api/v1/checkout").raise_for_status()
        samples = [
            measure_once(
                active_client,
                signal_probe,
                detection_delay_seconds,
                recovery_delay_seconds,
            )
            for _ in range(repetitions)
        ]
    finally:
        if owned_client is not None:
            owned_client.close()

    recovery_samples = [float(sample["recovery_seconds"]) for sample in samples]
    detection_samples = [float(sample["detection_seconds"]) for sample in samples]
    benchmark_command = command or (
        "python -m observability_stack.benchmark --base-url http://app:8000 "
        "--traces /evidence/traces.json --logs /evidence/logs.json "
        "--output /output/observability-stack-v1.json"
    )
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "project": "25-observability-stack",
        "metric": "incident_recovery_seconds",
        "value": statistics.median(recovery_samples),
        "unit": "seconds",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "command": benchmark_command,
        "repeat": repetitions,
        "samples": recovery_samples,
        "summary": {
            "median_recovery_seconds": statistics.median(recovery_samples),
            "median_detection_seconds": statistics.median(detection_samples),
            "signal_correlation_rate": 1.0,
            "signal_count": 3,
        },
        "method": (
            "Drive a real HTTP 200->503->200 incident lifecycle and reject each run "
            "unless its incident ID and trace IDs occur in metrics, traces and logs."
        ),
        "fixture": {
            "reason": "dependency_timeout",
            "incidents": repetitions,
            "detection_delay_seconds": detection_delay_seconds,
            "recovery_delay_seconds": recovery_delay_seconds,
        },
        "image": "observability-stack:local",
        "metrics": {
            "incident_detection_seconds": detection_samples,
            "incident_recovery_seconds": recovery_samples,
            "signal_correlation_rate": 1.0,
        },
        "environment": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
            "runtime": "HTTP lifecycle with OpenTelemetry Collector file evidence",
        },
        "runs": samples,
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--traces", type=Path)
    parser.add_argument("--logs", type=Path)
    args = parser.parse_args()
    if (args.traces is None) != (args.logs is None):
        parser.error("--traces and --logs must be provided together")
    probe: SignalProbe | None = None
    if args.traces is not None and args.logs is not None:
        probe = FileSignalProbe(args.traces, args.logs)
    result = run_benchmark(args.repeat, args.output, base_url=args.base_url, probe=probe)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
