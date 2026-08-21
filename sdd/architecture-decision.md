# Architecture Decision

## Status

Accepted: hexagonal modular monolith.

## Forces

The domain is small, integration pressure and auditability are high, and there is
no need for independent deployment, asynchronous fan-out or durable application
state. The proof needs real HTTP behavior plus three correlated signals.

## Decision

`domain.py` owns immutable incident state and time invariants. `application.py`
owns use cases over the narrow `IncidentStore` and `Clock` ports. FastAPI,
in-memory storage, Prometheus metrics, OpenTelemetry and the external benchmark
are adapters composed around those boundaries.

Dependency direction is always inward. Domain and application do not import
FastAPI, OpenTelemetry, Prometheus, Docker, storage engines, brokers or cloud
SDKs.

## Principles

- SRP: policy, HTTP, metrics, telemetry, storage and evidence validation have separate owners.
- OCP/DIP: storage and signal backends change through ports, OTLP or scrape configuration.
- LSP/ISP: the two-method store and callable clock are replaced in unit tests without semantic changes.
- KISS/YAGNI: one modular service; no microservices, broker, database or cloud dependency.
- DRY: lifecycle timing and invariants exist once in the application/domain path used by API and benchmark.

## Rejected alternatives

| Alternative | Reason |
|---|---|
| Metrics-only stack | Cannot prove trace/log correlation. |
| Microservices | Adds distribution without a deployability requirement. |
| Kafka or RabbitMQ | No queue, fan-out or asynchronous workload exists. |
| Persistent database | Persistence does not affect the instrumentation claim. |

## Consequences

The service remains easy to test and the Collector/backend can be replaced
without domain changes. Incident state resets with the process, and the local
benchmark must not be presented as a production SLO.
