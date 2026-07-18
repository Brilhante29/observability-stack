# Benchmark Plan: observability-stack

## Hypothesis

The service can demonstrate an observable failure lifecycle with a deterministic simulated MTTR of `1.2 minutes`.

## Command

```powershell
$env:PYTHONPATH = "src"
python -m observability_stack.benchmark --output benchmarks/results/observability-stack-v1.json
```

## Environment

- Runtime: Python 3.12 or the `observability-stack:local` image.
- Docker services: not required for the logical-clock result; optional for the API/dashboard path.
- Date: recorded in the JSON result.
- Host scheduling: excluded from the metric by design.

## Inputs

- Fixture: one controlled `dependency_timeout` incident.
- Dataset size: one incident per repetition.
- Repetitions: 3.
- Warmup: none; all times are logical.
- Seed: 42, recorded for fixture identity.

## Method

Open at logical `t=0s`, advance to `t=24s` and call `detect_failure`, advance to `t=72s` and call `recover_failure`. The primary metric is recovery time from open divided by 60. Repeating the same fixture demonstrates that the harness is deterministic.

## Metrics

| Metric | Unit | Source | Why it matters |
|---|---:|---|---|
| simulated_mttr_minutes | minutes | benchmark harness | primary portfolio claim |
| detection_seconds | seconds | incident state | shows time to detect |
| recovery_seconds | seconds | incident state | explains the primary result |

## Result schema

The versioned file `benchmarks/results/observability-stack-v1.json` includes project, schema version, metric, value, unit, timestamp, command, method, image, fixture, environment, samples and summary metrics. The expected value is `1.2` minutes and lower is better.

## Post angle

#25 observability-stack: a local FastAPI failure scenario whose Prometheus signals and logical-clock benchmark make detection and recovery reviewable without cloud credentials.
