# #25 observability-stack

**Prova:** observabilidade ponta a ponta em uma API local com falha controlada.

**Benchmark reproduzivel:** `simulated_mttr_minutes = 1.2 minutes` (deteccao em 24 s, recuperacao em 72 s).

O numero e uma simulacao deterministica de MTTR: o relogio logico abre o incidente em `t=0`, detecta em `t=24 s` e recupera em `t=72 s`. Ele demonstra o fluxo e o contrato da evidencia; nao e uma promessa de MTTR de producao.

## Inicio rapido

### Docker, somente a API

```powershell
docker build --tag observability-stack:local .
docker run --rm --publish 8000:8000 observability-stack:local
```

Abra `http://localhost:8000/docs` para o OpenAPI. O fluxo de falha pode ser exercitado assim:

```powershell
curl.exe http://localhost:8000/api/v1/checkout
curl.exe -X POST http://localhost:8000/api/v1/failure -H "Content-Type: application/json" -d '{"enabled":true,"reason":"dependency_timeout"}'
curl.exe http://localhost:8000/api/v1/checkout
curl.exe http://localhost:8000/api/v1/status
curl.exe -X POST http://localhost:8000/api/v1/failure -H "Content-Type: application/json" -d '{"enabled":false}'
```

O segundo `checkout` retorna `503` enquanto a falha esta ativa. A consulta a `/api/v1/status` representa a sonda de deteccao e atualiza o sinal de incidente.

### Docker Compose, com Prometheus e Grafana

```powershell
docker compose up --build
```

| Servico | Porta | Uso |
|---|---:|---|
| API | 8000 | OpenAPI, workload, falha e `/metrics` |
| Prometheus | 9090 | coleta a cada 5 s |
| Grafana | 3000 | dashboard provisionado |

O Grafana esta configurado para visualizacao anonima local, sem credenciais cloud. O dashboard mostra incidente ativo, taxa de requests por status, p95 de duracao e eventos do ciclo de vida.

### Execucao local sem Docker

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --requirement requirements-dev.txt
$env:PYTHONPATH = "src"
python -m observability_stack.cli
```

## Arquitetura e desacoplamento

```text
HTTP/FastAPI adapter -> ObservationService -> IncidentStore port -> in-memory adapter
                                  |
                                  +-> domain Incident / ControlledFailure

HTTP middleware -> Prometheus adapter -> /metrics -> Prometheus -> Grafana
```

O dominio em `src/observability_stack/domain.py` nao conhece FastAPI, Prometheus ou armazenamento. `ObservationService` depende de dois ports pequenos: `IncidentStore` e `Clock`. Isso aplica SRP e ISP; o adapter em memoria e o relogio logico sao substituiveis nos testes, evidenciando LSP. A composicao acontece no adapter FastAPI, aplicando DIP. O desenho evita broker, banco e cloud porque nenhum deles ajuda a provar este claim (KISS/YAGNI).

### Portas e adapters

| Boundary | Port | Adapter local | Proximo adapter possivel |
|---|---|---|---|
| Estado do incidente | `IncidentStore` | `InMemoryIncidentStore` | Redis/Postgres, se persistencia virar requisito |
| Tempo | `Clock` | `monotonic` na API; relogio logico no benchmark | relogio distribuido, se necessario |
| Transporte | endpoints REST | FastAPI/Uvicorn | outro adapter HTTP sem mover o caso de uso |
| Telemetria | metricas do adapter | `prometheus-client` | OpenTelemetry Collector, se houver necessidade de traces |

Prometheus e Grafana foram escolhidos porque fornecem coleta pull, linguagem de consulta operacional e dashboard local sem agente cloud pago. A aplicacao expoe metricas no formato Prometheus; o compose apenas conecta os adapters.

## Benchmark

O benchmark usa um fixture de um incidente `dependency_timeout`, seed `42`, tres repeticoes e relogio logico. O resultado versionado esta em [`benchmarks/results/observability-stack-v1.json`](benchmarks/results/observability-stack-v1.json).

```powershell
$env:PYTHONPATH = "src"
python -m observability_stack.benchmark --output benchmarks/results/observability-stack-v1.json
python -m json.tool benchmarks/results/observability-stack-v1.json
```

Depois de construir a imagem, o mesmo harness pode ser executado no container e gravado pelo shell:

```powershell
docker run --rm observability-stack:local benchmark > benchmarks/results/docker-run.json
```

O JSON inclui metodo, imagem, fixture, repeticoes, amostras e metricas de deteccao/recuperacao. Valores menores de `simulated_mttr_minutes` sao melhores, mas o valor atual e intencionalmente fixo para tornar a evidencia reproduzivel.

## Testes e CI

```powershell
$env:PYTHONPATH = "src"
python -m compileall -q src tests
python -m unittest discover -s tests -v
ruff check src tests
```

O workflow [`ci.yml`](.github/workflows/ci.yml) executa compilacao, testes, lint, valida o JSON do benchmark e constroi a imagem Docker. A validacao estrita local e:

```powershell
.\tools\validate-project.ps1 -SkipDocker
git diff --check
```

## Evidencia e limites

- O caminho default nao requer segredo, conta cloud ou servico externo alem do daemon Docker para o caminho Docker.
- O estado e em memoria e reinicia com o processo; isso e deliberado para o demo local.
- O MTTR e simulado por relogio logico e nao mede disponibilidade de uma plataforma de producao.
- Prometheus e Grafana sao imagens fixadas por tag no Compose; para reproducao de supply chain mais forte, fixe digests no ambiente de publicacao.

Veja [`REFERENCES.md`](REFERENCES.md), [`sdd/spec.md`](sdd/spec.md) e o artefato de verificacao OpenSpec em [`openspec/artifacts/verification.md`](openspec/artifacts/verification.md).
