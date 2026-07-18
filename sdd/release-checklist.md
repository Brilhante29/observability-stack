# Release Checklist

- [x] `docker build` path is documented in README.
- [x] `docker run` path is documented in README.
- [x] Benchmark command runs from a clean checkout after installing pinned dependencies.
- [x] Benchmark result is stored under `benchmarks/results/`.
- [x] README opens with number and result.
- [x] `REFERENCES.md` exists.
- [x] License exists.
- [x] No empty directories are used as proof.
- [x] No API key is required for the default path.
- [x] Post angle is written in `sdd/benchmark-plan.md` and README context.
- [x] Tests and `tools/validate-project.ps1 -SkipDocker` pass.
- [x] `git diff --check` passes.
