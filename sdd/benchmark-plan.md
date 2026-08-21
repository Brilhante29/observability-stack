# Benchmark Plan: observability-stack

## Hypothesis

Every measured incident can be correlated without gaps across metric, trace and
log evidence while preserving the real HTTP failure lifecycle.

## Canonical command

```powershell
docker compose -f docker-compose.evidence.yml up --build --abort-on-container-exit --exit-code-from benchmark
python tools/validate_benchmark.py benchmarks/results/observability-stack-v1.json
```

## Method

One warmup request precedes three measured incidents. Each run opens a unique
incident, observes the controlled `503`, waits 50 ms, detects it, waits another
50 ms, recovers it and confirms `200`. The API measures detection and recovery
from `time.monotonic()`.

The harness then requires:

- the incident ID and lifecycle trace IDs in OpenMetrics exemplars;
- the incident ID and all lifecycle trace IDs in Collector trace evidence;
- the incident ID and all lifecycle trace IDs in Collector log evidence.

## Metrics

| Metric | Unit | Gate |
|---|---:|---|
| `incident_recovery_seconds` | seconds | primary; lower is better |
| `incident_detection_seconds` | seconds | diagnostic |
| `signal_correlation_rate` | ratio | must equal `1.0` |

## Validity

The delays are real waits and the measurements are real server monotonic time.
The benchmark proves local instrumentation integrity, not production MTTR.
