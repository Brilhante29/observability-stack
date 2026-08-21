# Benchmark Proof

- Primary metric: `incident_recovery_seconds`; lower is better.
- Integrity gate: `signal_correlation_rate = 1.0`.
- Runs: three after one warmup request.
- Lifecycle: real `200 -> 503 -> 200` HTTP requests.
- Signals: OpenMetrics exemplars, OTLP traces and OTLP structured logs.
- Command: `docker compose -f docker-compose.evidence.yml up --build --abort-on-container-exit --exit-code-from benchmark`.
- Result: `benchmarks/results/observability-stack-v1.json`.
- Measured median: `incident_recovery_seconds = 0.1336 s`.
- Detection median: `incident_detection_seconds = 0.0712 s`.
- Correlation: `1.0` across metrics, traces and logs in all three runs.

The prior logical-clock value was rejected because it could not prove an
operational signal or measure real execution.
