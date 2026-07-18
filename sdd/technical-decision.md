# Technical Decision

## Status

Accepted

## Decision Type

stack, api-style, cloud, runtime, library

## Context

Project: `observability-stack #25`
Problem: make failure detection and recovery observable in a local demo.
Portfolio program: `backend-reliability-platform`
Public signal: a typed FastAPI backend with Prometheus metrics, Docker wiring and reproducible benchmark.
Benchmark: `simulated_mttr_minutes`

## Selected Option

Selected: Python 3.12 + FastAPI + prometheus-client + Uvicorn + Prometheus/Grafana Compose.

Reason:

The stack is small, common for operational HTTP services, exposes OpenAPI, and gives a direct Prometheus scrape endpoint without a paid dependency. Python also lets the benchmark reuse the application policy with a logical clock.

## Decision Brain Fields

- Stack profile: `fastapi-backend`
- API style: `rest-http`
- Messaging: `none`
- Cloud mode: `none`; this project has no cloud capability.
- Database/runtime: in-memory store, Python 3.12 slim, Uvicorn.
- Library policy: pin direct runtime dependencies; use standard library dataclasses, protocols and unittest for core behavior.

## Engineering Principles

Coupling boundary:

`domain.py` and `application.py` do not depend on framework, DB, broker, cloud SDK, transport or UI.

SOLID application:

- SRP: domain transitions, application use cases, in-memory storage, metrics and HTTP each have separate modules.
- OCP: storage and clock behavior extend through ports rather than modifying incident policy.
- LSP: `InMemoryIncidentStore` and the test store satisfy the same `IncidentStore` contract and preserve failure semantics.
- ISP: `IncidentStore` exposes only `get` and `put`; `Clock` is a callable port.
- DIP: `ObservationService` depends on `IncidentStore` and `Clock`, with composition at the API or benchmark adapter.

Simplicity:

- KISS: one process and one controlled failure are enough to show the signal path.
- YAGNI: no database, broker, cloud emulator, tracing collector or frontend was added.
- DRY: incident timing and recovery are implemented once and reused by API and benchmark.

Testability evidence:

- `tests/test_domain.py` runs use cases without FastAPI or Prometheus.
- `tests/test_api.py` verifies the HTTP and metrics contract.
- `tests/test_benchmark.py` locks the deterministic evidence number and schema fields.

## Rejected Options

| Option | Why rejected |
|---|---|
| Go + OpenTelemetry | A stronger production stack, but unnecessary complexity for this small Python-first portfolio signal. |
| SQLite/Postgres | State persistence is outside the local proof and would add migration/runtime cost. |
| Kumo/AWS | There is no cloud-backed capability in the product surface. |

## API Contract

Contract artifact: FastAPI-generated OpenAPI at `/openapi.json` and `/docs`.

Endpoints:

- `GET /healthz` and `GET /readyz` for runtime checks.
- `GET /api/v1/checkout` for the observable workload.
- `POST /api/v1/failure` to open/recover the controlled incident.
- `GET /api/v1/status` to represent the detection probe.
- `GET /metrics` for Prometheus exposition.

## Cloud Local-First

Local provider: none; no cloud capability is required.

Real provider target: none.

Config switch: `CLOUD_PROVIDER=none` is documented as the intentional default; a future provider must be introduced behind an adapter.

Unsupported behaviors: no claims of cloud parity or production durability.

## Benchmark Impact

Expected impact: expose a stable, reviewable `simulated_mttr_minutes` result with detection and recovery components.

Validation command:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m observability_stack.benchmark --output benchmarks/results/observability-stack-v1.json
```

## Operational Cost

- Docker services added: Prometheus and Grafana only.
- Local demo complexity: low.
- Failure case required: yes, controlled and reversible.

## Follow-up

Revisit storage and clock ports only if the project evolves from an educational local proof into a persistent service or a real incident measurement harness.
