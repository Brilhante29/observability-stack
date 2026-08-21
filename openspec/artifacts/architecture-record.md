# Architecture Record

Use a hexagonal modular monolith. Framework-free domain/application code depends
only on `IncidentStore` and `Clock`. HTTP, metric, telemetry, storage and
benchmark concerns are adapters. OTLP is the pluggable boundary between local
Collector and a future managed backend.

Microservices, broker, database and cloud SDK were rejected because none improves
the three-signal correlation proof.
