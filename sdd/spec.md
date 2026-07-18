# Spec: observability-stack

## Number

#25

## Claim

Este projeto prova observabilidade ponta a ponta em uma aplicacao local: falha controlada, metricas Prometheus, dashboard Grafana e evidencia de deteccao/recuperacao.

## Stack

Python 3.12, FastAPI, prometheus-client, Uvicorn, Prometheus, Grafana e Docker Compose.

## User-visible output

- Docker API: `docker build --tag observability-stack:local .` e `docker run --rm --publish 8000:8000 observability-stack:local`.
- Compose: API em `8000`, Prometheus em `9090`, Grafana em `3000`.
- Benchmark: `simulated_mttr_minutes = 1.2 minutes` em `benchmarks/results/observability-stack-v1.json`.

## Scope

In:

- Expor workload `/api/v1/checkout` e controle de falha `POST /api/v1/failure`.
- Expor metricas HTTP, falhas controladas e ciclo de vida de incidente.
- Rodar localmente com Docker e conectar Prometheus a Grafana.
- Gerar benchmark JSON deterministico e versionado.

Out:

- Persistencia de incidentes depois de reiniciar o processo.
- MTTR de uma plataforma real ou carga distribuida.
- Dependencia de segredo pago, cloud, broker ou banco.

## Architecture

`HTTP adapter -> application service -> ports -> local adapters`

O dominio e os casos de uso nao dependem de framework ou infraestrutura. O adapter FastAPI compoe `ObservationService`, `InMemoryIncidentStore`, relogio monotonic e metricas Prometheus.

## Failure scenario

1. Abrir `POST /api/v1/failure` com `enabled=true`.
2. Observar `503` no checkout e incremento de `observability_controlled_failures_total`.
3. Consultar `/api/v1/status`, que representa a sonda e registra deteccao.
4. Enviar `enabled=false` para recuperar e zerar `observability_active_incident`.

## Benchmark

- Primary metric: `simulated_mttr_minutes`.
- Unit: minutes; lower is better.
- Method: open at `t=0s`, detect at `t=24s`, recover at `t=72s`, repeat 3 times with logical clock.
- Command: `PYTHONPATH=src python -m observability_stack.benchmark --output benchmarks/results/observability-stack-v1.json`.
- Fixture: one `dependency_timeout`, seed `42`.
