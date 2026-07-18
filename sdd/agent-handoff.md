# Agent Handoff

Project: `25 - observability-stack`

## Principal Agent Summary

- Objective: turn the scaffold into a local-first observability demonstration.
- Portfolio program: `backend-reliability-platform`
- Public proof claim: observable controlled failure with reproducible simulated MTTR.
- Primary benchmark: `simulated_mttr_minutes`
- Default runnable path: `docker compose up --build`

## Subagent Decisions

| Role | Decision | Evidence Path | Status |
|---|---|---|---|
| `program-planner` | backend reliability signal | `project.yaml`, `sdd/spec.md` | done |
| `architecture-selector` | small hexagonal modular monolith | `sdd/architecture-decision.md` | done |
| `engineering-principles-reviewer` | ports isolate policy from adapters | `sdd/technical-decision.md` | done |
| `stack-decision-agent` | Python + FastAPI + Prometheus | `requirements.txt`, `sdd/technical-decision.md` | done |
| `api-style-agent` | REST with OpenAPI | `src/observability_stack/api.py` | done |
| `cloud-local-first-agent` | no cloud capability; local-only | `README.md`, `project.yaml` | done |
| `messaging-agent` | no broker | `sdd/technical-decision.md` | done |
| `language-profile-agent` | fastapi-backend | `project.yaml` | done |
| `benchmark-harness-agent` | logical clock, 3 repetitions | `src/observability_stack/benchmark.py` | done |
| `design-system-agent` | Prometheus/Grafana dashboard | `grafana/dashboards/observability-stack.json` | done |
| `security-reuse-reviewer` | no secrets; references recorded | `REFERENCES.md`, `sdd/reuse-improvement-review.md` | done |
| `release-ci-publisher` | CI, Docker and validation | `.github/workflows/ci.yml`, `tools/validate-project.ps1` | done |

## Local-First Runtime

- Docker command: `docker compose up --build`
- Local services: API `8000`, Prometheus `9090`, Grafana `3000`
- Kumo services, if any: none; this is not a cloud-backed project.
- Real cloud adapter target, if any: none.
- Config switch: `CLOUD_PROVIDER=none`; future providers must sit behind an adapter.
- Default path requires paid secret: no.

## Architecture Boundaries

- Domain boundary: immutable `Incident` and `ControlledFailure`.
- Use-case boundary: `ObservationService`.
- Ports: `IncidentStore` and `Clock`.
- Adapters: in-memory store, FastAPI/Uvicorn and Prometheus exporter.
- Dependency direction rule: adapters point inward; domain points to nothing external.

## Benchmark Handoff

- Metric: `simulated_mttr_minutes`.
- Unit: minutes.
- Higher or lower is better: lower.
- Command: `PYTHONPATH=src python -m observability_stack.benchmark --output benchmarks/results/observability-stack-v1.json`.
- Result path: `benchmarks/results/observability-stack-v1.json`.
- Dataset or fixture: one deterministic `dependency_timeout` incident, seed `42`.

## Open Risks

- The in-memory adapter resets on restart.
- The metric is a deterministic simulation and must not be described as production MTTR.

## Publication Gates

- [x] Docker path documented.
- [x] benchmark result exists.
- [x] README starts with project number, claim and benchmark.
- [x] references are documented.
- [x] no secret in files or git remote.
- [x] validation and diff checks are part of the release procedure.
