# Spec: observability-stack

## Number and claim

#25 proves end-to-end correlation for one controlled incident across metrics,
traces and logs in a local-first stack.

## Acceptance criteria

1. A baseline checkout returns `200`, the controlled failure returns `503`, and recovery restores `200`.
2. Opened, detected and recovered lifecycle responses expose valid trace IDs.
3. The same incident and trace IDs exist in OpenMetrics, OTLP trace evidence and OTLP log evidence.
4. Three measured runs produce `signal_correlation_rate = 1.0`.
5. The full Compose provisions Prometheus, Tempo, Loki and Grafana with immutable external images.

## Boundaries

The domain owns incident identity, timing invariants and immutable transitions.
The application owns use cases and depends on `IncidentStore` and `Clock`.
FastAPI, metrics, telemetry, storage and benchmark verification are adapters.

## Non-goals

Production SLOs, durable incident management, distributed load, cloud parity,
broker-based messaging and persistent application storage are not claimed.
