# Agent Handoff

Project: `25 - observability-stack`

## Current state

- Macro: `delivery-observability-infra`.
- Claim: one controlled incident correlated across metrics, traces and logs.
- Architecture: hexagonal modular monolith.
- Metric: `incident_recovery_seconds`; mandatory gate `signal_correlation_rate = 1.0`.
- Canonical result: `benchmarks/results/observability-stack-v1.json`.

## Implemented

- Real `200 -> 503 -> 200` HTTP scenario with monotonic server timing.
- OpenMetrics exemplars and explicit OpenTelemetry traces/logs.
- Collector evidence exporters plus full Prometheus/Tempo/Loki/Grafana Compose.
- Fail-closed JSON validator, 16 tests, 91% coverage and reusable Python CI.
- Digest-pinned runtime images and non-root application image.

## Validation state

- Passed: 16 unit/contract tests, Ruff, 91% coverage, two Compose model parses,
  `git diff --check` and application image build.
- Pending: create the clean source commit, run the V2 producer, publish and
  verify exact-head GitHub CI.
- Block cause: privileged-command quota until 2026-08-21 00:36 -03:00, not a
  repository defect.

## Next exact commands

```powershell
git add --all
git commit -m "feat: correlate incident metrics traces and logs"
python tools/benchmark_v2.py
python tools/validate_benchmark.py benchmarks/results/observability-stack-v1.json
python tools/validate-publication.py
```

After those pass, replace the README benchmark headline with the measured median,
set `status: published`, complete OpenSpec/release gates, commit V1/V2, push,
verify exact-head CI and promote the reusable observability contract/skill into
`portfolio-reuse-kit`.
