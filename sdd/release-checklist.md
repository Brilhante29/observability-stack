# Release Checklist

- [x] `docker build` path is documented in README.
- [x] `docker run` path is documented in README.
- [x] Benchmark command runs from a clean source commit with the evidence Compose.
- [x] Benchmark result is stored under `benchmarks/results/`.
- [x] README opens with project number and integrity metric.
- [x] `REFERENCES.md` exists.
- [x] License exists.
- [x] No empty directories are used as proof.
- [x] No API key is required for the default path.
- [x] Post angle is written in `sdd/benchmark-plan.md` and README context.
- [x] Equivalent local gates pass; strict mypy ran in the pinned Python 3.12 image.
- [x] Unit/contract tests, Ruff and 90% coverage gate pass.
- [x] `git diff --check` passes.
- [x] Full Prometheus/Tempo/Loki/Grafana profile passes backend navigation checks.
