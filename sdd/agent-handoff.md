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

- Passed: 16 unit/contract tests, Ruff, strict mypy over 11 files, 91% coverage,
  two Compose model parses, `git diff --check`, application image build and V1/V2
  evidence validation.
- Full profile passed: all five endpoints healthy, Prometheus target `up`, three
  Grafana datasources plus dashboard provisioned, trace retrievable from Tempo,
  and all three lifecycle events retrievable from Loki.
- Tempo 3.0 removed legacy `ingester` and `compactor` blocks; the committed
  configuration follows the monolithic migration contract.
- Evidence and output use named volumes initialized with UID `10001`; CI copies
  the result from the stopped benchmark container before teardown.
- Reuse promotion passed in `portfolio-reuse-kit` commit `845560a` and CI run
  `32446626119`. The central publication record owns the final metadata-head CI.

## Next exact commands

```powershell
git add --all
git commit -m "docs: publish correlated observability evidence"
git push origin HEAD:main
gh run list --repo Brilhante29/observability-stack --commit <sha>
```

No project implementation gate remains. The next portfolio repository is #27
`terraform-aws-baseline`.
