# Reuse Map: #25 observability-stack

## Kit Inputs

| Concern | Source of truth | Project use |
|---|---|---|
| Agent skills | `.codex/skills/` and `.claude/skills/` | language, architecture, benchmark and release workflow |
| Architecture | `.portfolio/architecture/decision-matrix.yaml` | hexagonal modular monolith decision |
| Stack and libraries | `.portfolio/decision-brain/stack-matrix.yaml` | FastAPI and Prometheus selection |
| API style | `.portfolio/decision-brain/api-style-matrix.yaml` | REST/OpenAPI contract |
| Benchmark contract | `.portfolio/contracts/benchmark-result.schema.json` | versioned JSON evidence |
| OpenSpec workflow | `openspec/config.yaml` and `.portfolio/openspec/` | intent through verification artifacts |

## Evidence Map

| Evidence | Location | State |
|---|---|---|
| Specification | `sdd/spec.md` | complete |
| Architecture decision | `sdd/architecture-decision.md` | complete |
| Technical decision | `sdd/technical-decision.md` | complete |
| Benchmark plan and result | `sdd/benchmark-plan.md`, `benchmarks/results/observability-stack-v1.json` | complete |
| OpenSpec verification | `openspec/artifacts/verification.md` | complete |
| Reuse review | `sdd/reuse-improvement-review.md` | complete |
| Runtime proof | `Dockerfile`, `docker-compose.yml`, `prometheus.yml`, `grafana/` | complete |

This inventory records the project-level proof without modifying the shared kit.
