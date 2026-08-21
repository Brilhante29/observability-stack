# #25 observability-stack

**Prova:** um incidente HTTP real e encontrado pelo mesmo `incident_id` em metricas, traces e logs.

**Benchmark reproduzivel:** `incident_recovery_seconds = 0.1336 s` (mediana),
com `signal_correlation_rate = 1.0` em `3/3` execucoes.

O harness executa `200 -> 503 -> 200`, repete tres vezes e falha se um
`incident_id` ou qualquer trace de ciclo de vida desaparecer de um sinal.

## Execute a prova

```powershell
docker compose -f docker-compose.evidence.yml up --build --abort-on-container-exit --exit-code-from benchmark
python tools/validate_benchmark.py benchmarks/results/observability-stack-v1.json
docker compose -f docker-compose.evidence.yml down --volumes
```

Esse caminho sobe somente API + OpenTelemetry Collector + benchmark. O resultado
fica em `benchmarks/results/observability-stack-v1.json`.

## Explore a stack

API isolada com um `docker run`:

```powershell
docker build --tag observability-stack:local .
docker run --rm --publish 8000:8000 observability-stack:local
```

Stack completa:

```powershell
docker compose up --build
```

| Servico | Porta | Responsabilidade |
|---|---:|---|
| FastAPI | 8000 | workload, falha controlada, status e OpenMetrics |
| Prometheus | 9090 | scrape, series e exemplars com `trace_id` |
| Tempo | 3200 | armazenamento e consulta de traces |
| Loki | 3100 | armazenamento de logs OTLP estruturados |
| Grafana | 3000 | navegacao provisionada entre os tres sinais |
| OTel Collector | interna | roteamento OTLP para Tempo, Loki e evidencia |

Todas as imagens externas possuem versao e digest. O caminho default nao usa
segredo, conta cloud, broker ou banco.

## Contrato HTTP

```powershell
curl.exe http://localhost:8000/api/v1/checkout
curl.exe -X POST http://localhost:8000/api/v1/failure `
  -H "Content-Type: application/json" -H "X-Correlation-ID: incident-demo-001" `
  -d '{"enabled":true,"incident_id":"incident-demo-001","reason":"dependency_timeout"}'
curl.exe http://localhost:8000/api/v1/checkout -H "X-Correlation-ID: incident-demo-001"
curl.exe http://localhost:8000/api/v1/status -H "X-Correlation-ID: incident-demo-001"
curl.exe -X POST http://localhost:8000/api/v1/failure `
  -H "Content-Type: application/json" -H "X-Correlation-ID: incident-demo-001" `
  -d '{"enabled":false,"incident_id":"incident-demo-001"}'
```

Cada resposta devolve `X-Correlation-ID` e `X-Trace-ID`. O checkout intermediario
retorna `503`; depois da recuperacao volta a `200`.

## Arquitetura

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

O dominio nao importa FastAPI, OpenTelemetry, Prometheus, storage, broker ou
cloud SDK. `ObservationService` depende somente de `IncidentStore` e `Clock`.
Isso preserva DIP/ISP, deixa LSP verificavel com adapters alternativos e mantem
SRP entre politica, transporte e telemetria. Um monolito modular resolve o
problema sem microservicos, Kafka, RabbitMQ ou banco (KISS/YAGNI).

O adapter fala OTLP padrao. Trocar o Collector local por um endpoint real exige
somente `OTEL_EXPORTER_OTLP_ENDPOINT`, sem alterar dominio ou caso de uso.

## Benchmark

```powershell
python tools/validate_benchmark.py benchmarks/results/observability-stack-v1.json
```

O JSON registra as tres amostras, deteccao, recuperacao, IDs de incidente, tres
trace IDs de ciclo de vida por execucao, ambiente, comando e presenca em cada
sinal. Menor `incident_recovery_seconds` e melhor; `signal_correlation_rate`
precisa ser exatamente `1.0`.

Resultado canonico: recuperacao mediana de `0.1336 s`, deteccao mediana de
`0.0712 s` e nenhuma falha de correlacao em nove verificacoes de sinal.

Os atrasos de 50 ms entre abrir, detectar e recuperar sao esperas reais do
harness, nao avancos de relogio logico. O resultado demonstra integridade de
instrumentacao local, nao MTTR, retencao ou alta disponibilidade de producao.

## Qualidade e CI

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
ruff check src tests tools
coverage run --branch -m unittest discover -s tests
coverage report --fail-under=90
docker compose config --quiet
docker compose -f docker-compose.evidence.yml config --quiet
```

A CI reutiliza o perfil Python imutavel de `ci-cd-templates` e possui um job
separado que constroi a imagem, executa o Compose de evidencia e valida o JSON.
No estado atual sao `16` testes e `91%` de cobertura no nucleo testavel.

Detalhes: [decisao arquitetural](sdd/architecture-decision.md),
[plano do benchmark](sdd/benchmark-plan.md) e [referencias](REFERENCES.md).
