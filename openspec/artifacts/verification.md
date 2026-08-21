# Verification: #25 observability-stack

| Gate | Evidence | Status |
|---|---|---|
| Unit and contract tests | `python -m unittest discover -s tests -v` | passed: 16 |
| Ruff | `ruff check src tests tools` | passed |
| Core coverage | `coverage report --fail-under=90` | passed: 91% |
| Compose models | full and evidence `config --quiet` | passed |
| Application image | Python 3.12.13 digest-pinned build | passed |
| Whitespace | `git diff --check` | passed |
| Correlated evidence runtime | evidence Compose | pending privileged Docker access |
| Versioned V1 benchmark | JSON validator | pending runtime result |
| Exact-head GitHub CI | two jobs | pending publication |

The remaining gates are explicitly runtime/publication gates. No logical-clock
result is accepted as substitute evidence.
