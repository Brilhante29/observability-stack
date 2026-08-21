---
name: github-actions-reusable-workflow
description: Build or audit reusable GitHub Actions workflows for Python, Go, Node, JVM Gradle, or Terraform repositories. Use when Codex must select a stack-specific CI profile, secure workflow_call boundaries, prove the template through an executable fixture, or publish exact-head CI evidence without mutable refs or arbitrary command inputs.
---

# GitHub Actions Reusable Workflow

## Workflow

1. Read the project's problem, stack decision, lockfiles, test commands, and benchmark contract. Select only the runtime profile the project actually needs.
2. Reuse a stack workflow by immutable 40-character source commit. Keep stack commands explicit inside the called workflow; never accept an arbitrary shell command as input.
3. Require `workflow_call`, read-only permissions, a timeout inside the called job, full-SHA action pins, and `persist-credentials: false` on checkout.
4. Execute the workflow against a minimal repository-owned fixture. Static YAML validation alone does not prove that install, lint, type, test, build, or validation commands work.
5. Run actionlint, zizmor, and repository-local policy checks without credentials. Fail when the template produces any finding.
6. Publish the stack profile under `ci-profile-v1` and record successful GitHub Actions evidence for the exact final head.

## Measurement Boundary

- Benchmark deterministic guardrail scan latency separately from hosted build duration.
- Compare build times only under the same runner, cache state, dependency set, workload, and repetition policy.
- Keep every sample and immutable source/image/dependency provenance in benchmark result V2.

## Reject

Reject mutable action or workflow refs, write-all permissions, persisted checkout credentials, unbounded jobs, secrets in the default path, arbitrary command inputs, missing lockfiles where the ecosystem supports them, fixtures that do not execute the profile, or publication evidence from a different head.
