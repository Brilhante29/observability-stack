# Technical Decision

## Selected stack

Python 3.12.13, FastAPI, prometheus-client, OpenTelemetry SDK/Collector,
Prometheus, Tempo, Loki, Grafana and Docker Compose.

## Why this stack

FastAPI keeps the failure workload typed and inspectable. OpenMetrics exemplars
connect metrics to trace IDs. OTLP decouples the app from local Tempo/Loki and
from future managed backends. Grafana provisions navigation across all signals.

Direct Python dependencies and every external image are pinned. The app runs as
UID 10001 on a digest-pinned Python base.

## Protocol decisions

- REST fits imperative failure control and status reads; GraphQL adds no useful query shape here.
- OTLP HTTP carries traces and logs to the Collector.
- Prometheus pull scrapes OpenMetrics from `/metrics`.
- Messaging is `none` because the lifecycle is synchronous.
- Cloud is pluggable through `OTEL_EXPORTER_OTLP_ENDPOINT`; no provider SDK enters the app.

## Runtime profiles

`docker-compose.evidence.yml` is the fast, fail-closed proof path with API,
Collector and benchmark. `docker-compose.yml` is the exploration path with
Prometheus, Tempo, Loki and Grafana.

## Quality gates

The shared immutable Python CI profile runs lint, strict mypy and 90% coverage.
A project job builds the container, runs the evidence Compose, validates three
signals for all three repetitions and tears down volumes even on failure.
