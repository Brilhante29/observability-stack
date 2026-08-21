# Verification: #25 observability-stack

| Gate | Evidence | Status |
|---|---|---|
| Unit and contract tests | `python -m unittest discover -s tests -v` | passed: 16 |
| Ruff | `ruff check src tests tools` | passed |
| Core coverage | `coverage report --fail-under=90` | passed: 91% |
| Compose models | full and evidence `config --quiet` | passed |
| Application image | Python 3.12.13 digest-pinned build | passed |
| Strict typing | mypy 2.3.1 in Python 3.12 container | passed: 11 files |
| Whitespace | `git diff --check` | passed |
| Correlated evidence runtime | evidence Compose | passed: 3/3 runs, all signals |
| Cross-platform evidence permissions | named volumes owned by UID `10001` | passed locally and on Ubuntu CI |
| Versioned V1/V2 benchmark | contract and publication validators | passed |
| Full exploration runtime | app, Prometheus, Tempo 3, Loki and Grafana | passed |
| Backend navigation | Prometheus target, Tempo trace, Loki events, Grafana provisioning | passed |
| Code-bearing GitHub CI | two jobs | passed: run `32446255631` |
| Reuse promotion | kit contract, fixtures and mirrored skill | passed: kit `845560a`, run `32446626119` |

The full runtime reproduced `200 -> 503 -> 200`, returned the recovery trace
from Tempo, found `opened`, `detected` and `recovered` in Loki, reported the
Prometheus target as `up`, and provisioned all three Grafana datasources plus the
dashboard. No logical-clock result is accepted as substitute evidence.
