# Architecture Decision

## Status

Accepted

## Context

Project: `observability-stack #25`
Claim: observabilidade ponta a ponta
Benchmark: `simulated_mttr_minutes`

Problem forces:

- Domain complexity: low
- Integration pressure: medium because HTTP, Prometheus and dashboard must be wired.
- UI state complexity: none
- Data/ML reproducibility: high for the logical-clock benchmark.
- Auditability/event history: medium through incident timestamps and Prometheus counters.
- Throughput/async pressure: low
- Independent deployability need: low; one container is the intended proof.

## Decision

Chosen architecture: small hexagonal modular monolith.

Reason:

The claim is about operational signals and recovery behavior, not distributed topology. A single service keeps the demo local and repeatable while making domain/application boundaries explicit. `domain.py` owns immutable incident transitions, `application.py` owns use cases and ports, and adapters own HTTP, storage and metrics.

Dependency rule:

Domain and application code do not import FastAPI, Prometheus, storage engines, brokers, cloud SDKs or UI. Adapters depend inward on ports and are composed at the API boundary.

## Rejected Alternatives

| Alternative | Why rejected |
|---|---|
| Microservices | Adds network and deployment failure modes without improving the local MTTR proof. |
| Event-driven with broker | No asynchronous fan-out or durable event stream is needed for this scenario. |
| Full OpenTelemetry Collector stack | Useful for traces, but more moving parts than the claim needs; Prometheus metrics are sufficient. |

## Folder Layout

```text
src/observability_stack/
  domain.py
  ports.py
  application.py
  api.py
  benchmark.py
  infrastructure/
tests/
benchmarks/results/
prometheus.yml
grafana/
```

## Testing Strategy

- Unit tests: pure incident state and `ObservationService` with a manual clock/store.
- Contract tests: FastAPI health, checkout, failure toggle, status and Prometheus exposition.
- Benchmark: same application service with a deterministic logical clock and a fixed fixture.

## Consequences

Positive:

- The public runtime is easy to start and inspect with curl, OpenAPI, Prometheus and Grafana.
- The benchmark number is independent of host scheduling and network latency.
- A future Redis/Postgres adapter can be added without changing domain policy.

Tradeoffs:

- Incident state is process-local and resets on restart.
- The MTTR number is a simulation, not a production SLO measurement.

Migration path:

Add a durable `IncidentStore` adapter and a real probe/clock only when a persistence or production-like measurement requirement is demonstrated.
