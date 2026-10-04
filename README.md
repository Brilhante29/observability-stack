# Observability Stack: One Incident, Traced across Metrics, Traces, and Logs

**`incident_recovery_seconds = 0.1336 s` (median) with `signal_correlation_rate = 1.0` in `3/3` runs.** A real HTTP incident (`200 -> 503 -> 200`) is found by the same `incident_id` in Prometheus metrics, Tempo traces, and Loki logs, and the harness fails if any signal loses it.

[![CI](https://github.com/Brilhante29/observability-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/Brilhante29/observability-stack/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-425CC7?logo=opentelemetry&logoColor=white) ![Grafana](https://img.shields.io/badge/Grafana-F46800?logo=grafana&logoColor=white) ![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white)

## Why this exists

During an incident, the expensive part is not seeing that something is red: it is getting from the red graph to the exact failing request and its log lines. Dashboards, traces, and logs are often set up by different people, and the identifiers that would connect them get lost at some hop. "We have observability" then means three disconnected tools. This repository proves the connection end to end:

- a FastAPI service exposes a controlled failure switch, so a real incident can be opened and closed on demand;
- every response returns `X-Correlation-ID` and `X-Trace-ID`, and the same IDs reach Prometheus exemplars, Tempo traces, and Loki logs through OpenTelemetry;
- an external benchmark opens the incident, detects it, recovers it, and verifies that the `incident_id` and all three lifecycle traces appear in **every** signal;
- the benchmark fails closed when any signal is missing anything.

## Results

| Metric | Result |
|---|---:|
| Median recovery (`incident_recovery_seconds`) | 0.1336 s |
| Median detection | 0.0712 s |
| Signal correlation rate | 1.0 (no failures in nine signal checks) |
| Runs | 3/3 |

The 50 ms waits between opening, detecting, and recovering are real harness sleeps, not logical clock jumps. The result demonstrates local instrumentation integrity, not production MTTR, retention, or high availability. The JSON records all samples, incident IDs, lifecycle trace IDs per run, environment, command, and presence in each signal.

## Quickstart

Evidence path (API + OpenTelemetry Collector + benchmark only):

```bash
docker compose -f docker-compose.evidence.yml up --build --abort-on-container-exit --exit-code-from benchmark
docker compose -f docker-compose.evidence.yml cp benchmark:/output/observability-stack-v1.json benchmarks/results/observability-stack-v1.json
python tools/validate_benchmark.py benchmarks/results/observability-stack-v1.json
docker compose -f docker-compose.evidence.yml down --volumes
```

Named volumes keep UID `10001` working on Windows and Linux.

Full exploration stack:

```bash
docker compose up --build
```

| Service | Port | Responsibility |
|---|---:|---|
| FastAPI | 8000 | Workload, controlled failure, status, OpenMetrics |
| Prometheus | 9090 | Scrape, series, and exemplars with `trace_id` |
| Tempo | 3200 | Trace storage and query |
| Loki | 3100 | Structured OTLP log storage |
| Grafana | 3000 | Provisioned navigation across the three signals |
| OTel Collector | internal | OTLP routing to Tempo, Loki, and evidence files |

Every external image is pinned by version and digest. The default path needs no secret, cloud account, broker, or database.

Walk through an incident by hand:

```bash
curl http://localhost:8000/api/v1/checkout
curl -X POST http://localhost:8000/api/v1/failure \
  -H "Content-Type: application/json" -H "X-Correlation-ID: incident-demo-001" \
  -d '{"enabled":true,"incident_id":"incident-demo-001","reason":"dependency_timeout"}'
curl http://localhost:8000/api/v1/checkout -H "X-Correlation-ID: incident-demo-001"   # 503
curl http://localhost:8000/api/v1/status -H "X-Correlation-ID: incident-demo-001"
curl -X POST http://localhost:8000/api/v1/failure \
  -H "Content-Type: application/json" -H "X-Correlation-ID: incident-demo-001" \
  -d '{"enabled":false,"incident_id":"incident-demo-001"}'
```

## How it works

```text
FastAPI adapter -----------> ObservationService -----------> IncidentStore port
      |                              |                              |
      |                              +----> Incident domain          +-> memory
      |
      +-> Metrics adapter -> OpenMetrics -> Prometheus
      +-> Telemetry adapter -> OTLP -> Collector -> Tempo / Loki
                                             |
                                             +-> evidence files

External benchmark -> HTTP + /metrics + evidence files -> fail closed
```

The domain imports no FastAPI, OpenTelemetry, Prometheus, storage, broker, or cloud SDK; `ObservationService` depends only on `IncidentStore` and `Clock`. The adapter speaks standard OTLP, so moving from the local Collector to a real backend only changes `OTEL_EXPORTER_OTLP_ENDPOINT`.

## Design decisions

| Decision | Why | Rejected |
|---|---|---|
| OpenTelemetry end to end | Vendor-neutral IDs that survive every hop | Separate SDKs per backend |
| Fast evidence stack separate from the full Grafana stack | CI proves correlation in seconds; humans explore with the full stack | Running five services for every check |
| Controlled failure switch | Incidents are reproducible on demand | Waiting for organic failures |
| Modular monolith | One service is enough to prove signal correlation | Microservices, Kafka, or a database for a telemetry proof |

## Testing

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
ruff check src tests tools
coverage run --branch -m unittest discover -s tests && coverage report --fail-under=90
docker compose config --quiet
docker compose -f docker-compose.evidence.yml config --quiet
```

CI reuses the immutable Python profile from [ci-cd-templates](https://github.com/Brilhante29/ci-cd-templates) and runs a separate job that builds the image, executes the evidence Compose file, and validates the JSON. Currently 16 tests and 91% coverage on the testable core.

## Limitations

- In-memory incident store; state does not survive restarts.
- Local single-host stack; retention, sampling, and backend scaling are not evaluated.
- Recovery time is driven by harness sleeps, so it validates instrumentation, not response time of an on-call team.

## Project structure

```text
src/observability_stack/   domain, ports, application, API, infrastructure (metrics, telemetry), benchmark, CLI
tests/                     domain, service, adapter, and benchmark tests
config/                    OpenTelemetry Collector, Tempo, and Loki configuration
grafana/                   provisioned data sources and dashboards
benchmarks/  tools/        results, benchmark and publication validators
sdd/  openspec/            architecture decision, benchmark plan, handoff
```

## How this repository is built

The project follows the spec-driven workflow of [portfolio-reuse-kit](https://github.com/Brilhante29/portfolio-reuse-kit). Details: [architecture decision](sdd/architecture-decision.md) and [benchmark plan](sdd/benchmark-plan.md); [`project.yaml`](project.yaml) records the stack and rejected alternatives. Development is AI-assisted and human-governed: [`AGENTS.md`](AGENTS.md) and [`CLAUDE.md`](CLAUDE.md) hold the coding-agent instructions, while tests, validators, and CI decide what gets published.

## Related work

- [api-gateway-lite](https://github.com/Brilhante29/api-gateway-lite): W3C trace propagation at the edge.
- [vision-serving-fastapi](https://github.com/Brilhante29/vision-serving-fastapi): Prometheus metrics on a model-serving API.

See [`REFERENCES.md`](REFERENCES.md) for sources.

## Author

**Guilherme Brilhante**, software engineer working on scalable backends and production AI.
[LinkedIn](https://www.linkedin.com/in/guilhermefreirebrilhanteseveriano/) · [GitHub](https://github.com/Brilhante29) · [Publications](https://dblp.org/pid/353/6812.html)

## License

[MIT](LICENSE).
