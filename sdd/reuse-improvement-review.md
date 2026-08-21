# Reuse Improvement Review

Project: `25 - observability-stack`

## Review points

- [x] after scaffold
- [x] after architecture decision
- [x] after first working slice
- [x] after benchmark redesign
- [x] before publication
- [x] after CI definition

## Findings

| Finding | Classification | Kit area | Action | Status |
|---|---|---|---|---|
| The old harness could publish a fabricated logical MTTR without checking real signals. | `patch_now` | benchmark contract | Require measured HTTP lifecycle, per-run signal booleans and correlation rate. | implemented in project; kit promotion pending |
| Observability projects need two Compose profiles: fast evidence and full exploration. | `patch_now` | component pack | Record this split and its fail-closed CI pattern. | implemented; promotion pending |
| OTLP provides the right cloud abstraction without a fake provider adapter. | `patch_now` | stack decision | Add OTLP endpoint as the local-to-real switch. | implemented; promotion pending |
| Major backend upgrades need a real startup gate, not only Compose parsing. | `patch_now` | validation skill | Require backend health and navigation checks for the exploration profile. | implemented; promotion pending |
| Bind-mounted evidence can pass on Windows and fail for UID `10001` on Linux CI. | `patch_now` | Docker harness | Seed named volumes from the non-root image and copy results explicitly. | implemented; promotion pending |
| Source-locked evidence cannot verify an older commit from a depth-1 checkout. | `patch_now` | publication CI | Fetch full history before validating historical provenance. | implemented; promotion pending |
| Kafka, RabbitMQ, database and Kumo add no evidence to this claim. | `reject` | architecture | Keep them out until a product force requires them. | rejected |

## Final gate

- [x] Reusable improvements were patched or recorded.
- [x] Project-specific implementation was not moved into the kit.
- [x] Validation reflects Python, Docker Compose and three-signal benchmark checks.
