# Benchmark Proof

- Metric: `simulated_mttr_minutes`
- Result: `1.2 minutes`
- Method: open at `t=0s`, detect at `t=24s`, recover at `t=72s`, repeat three times.
- Fixture: one `dependency_timeout` incident, seed `42`.
- Command: `PYTHONPATH=src python -m observability_stack.benchmark --output benchmarks/results/observability-stack-v1.json`
- Result path: `benchmarks/results/observability-stack-v1.json`
- Direction: lower is better.

The JSON also records detection seconds, recovery seconds, environment, image, command and method so the number is auditable without a cloud service.
