# Reuse Map: #25 observability-stack

## Kit Inputs

The project consumes the local portfolio catalog, decision brain, language profile, OpenSpec schema, benchmark schema, SDD templates and strict validation tool. The original reusable contracts remain in `.portfolio/` and `.portfolio-control/`.

## Project Delta

| Delta | Why it is project-specific or reusable | Action |
|---|---|---|
| Logical-clock incident benchmark | Project-specific proof of this controlled failure lifecycle; reusable method may be promoted later. | `backlog` |
| CI validation of benchmark evidence plus Docker build | Reusable release pattern for local observability projects. | `patch_now` in this repository; kit change not required |
| No cloud adapter | The product has no cloud capability; adding one would be decorative infrastructure. | `reject` |

## Coupling Rule

Domain code must not depend on infrastructure adapters, providers, brokers, HTTP frameworks or model vendors. Dependencies point inward through stable ports. Reuse is accepted only when it reduces duplication without making the problem less clear.
