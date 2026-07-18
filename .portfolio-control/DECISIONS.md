# Decision Register: #25 observability-stack

| Decision | Selected option | Evidence or reason | Revisit trigger |
|---|---|---|---|
| Architecture | small hexagonal modular monolith | one local process with explicit ports/adapters | persistence or distributed deployment becomes a measured requirement |
| API style | REST/OpenAPI | fixed workload and command endpoints; easy curl and scrape inspection | client shape becomes graph-oriented |
| Messaging | none | no asynchronous fan-out or durable queue is in scope | async delivery is proven necessary |
| Storage | in-memory | the benchmark needs one deterministic incident, not durability | restart persistence is required |
| Local-first/cloud | none | this project has no cloud-backed capability | a cloud adapter becomes part of the product |
| Libraries | FastAPI, prometheus-client, Uvicorn, httpx | direct fit for API, metrics, runtime and contract tests | dependency maintenance or benchmark bottleneck |

## Design Principles

- **SRP:** domain, application, storage, metrics and HTTP have separate reasons to change.
- **OCP:** storage and clock behavior extend through ports.
- **LSP:** test and runtime stores preserve the `IncidentStore` contract.
- **ISP:** ports expose only `get`, `put` and a callable clock.
- **DIP:** use cases depend on abstractions and adapters are composed at the edge.
- **DRY:** timing policy is reused by API and benchmark; business knowledge is not duplicated.
- **KISS/YAGNI:** no broker, database, cloud emulator or tracing stack without a claim that needs it.
- **Law of Demeter:** application code talks to its direct store port, not to adapter internals.
