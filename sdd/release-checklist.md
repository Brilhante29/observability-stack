# Release Checklist

- [x] `docker build` path is documented in README.
- [x] `docker run` path is documented in README.
- [ ] Benchmark command runs from a clean checkout with the evidence Compose.
- [ ] Benchmark result is stored under `benchmarks/results/`.
- [x] README opens with project number and integrity metric.
- [x] `REFERENCES.md` exists.
- [x] License exists.
- [x] No empty directories are used as proof.
- [x] No API key is required for the default path.
- [x] Post angle is written in `sdd/benchmark-plan.md` and README context.
- [ ] Full `tools/validate-project.ps1 -SkipDocker` passes after V1 evidence exists.
- [x] Unit/contract tests, Ruff and 90% coverage gate pass.
- [x] `git diff --check` passes.
