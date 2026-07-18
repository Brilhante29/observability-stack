# Architecture Record

Use a small hexagonal modular monolith. `domain.py` contains framework-free immutable incident transitions. `application.py` owns `ObservationService` and depends only on `IncidentStore` and `Clock` ports. FastAPI, in-memory state and Prometheus are adapters composed outside the policy.

This structure applies SRP, ISP and DIP directly, keeps LSP testable with alternate store/clock implementations, and follows KISS/YAGNI by excluding a broker, database, cloud emulator and tracing collector. Unit tests execute the application without HTTP or infrastructure.
