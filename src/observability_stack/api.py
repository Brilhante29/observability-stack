"""FastAPI adapter for the observable checkout demo."""

from __future__ import annotations

from time import monotonic, perf_counter
from typing import Any

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

from .application import ObservationService
from .domain import ControlledFailure
from .infrastructure import metrics
from .infrastructure.store import InMemoryIncidentStore


class FailureRequest(BaseModel):
    enabled: bool = Field(description="Enable or disable the controlled failure.")
    reason: str = Field(default="dependency_timeout", min_length=3, max_length=80)


def create_app() -> FastAPI:
    service = ObservationService(InMemoryIncidentStore(), monotonic)
    app = FastAPI(
        title="#25 Observability Stack",
        version="1.0.0",
        description="A local-first service with Prometheus metrics and a controlled incident.",
    )

    @app.middleware("http")
    async def record_http_metrics(request: Any, call_next: Any) -> Response:
        started = perf_counter()
        path = request.url.path
        try:
            response = await call_next(request)
        except Exception:
            metrics.REQUESTS.labels(request.method, path, "500").inc()
            metrics.REQUEST_DURATION.labels(request.method, path).observe(perf_counter() - started)
            raise
        metrics.REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        metrics.REQUEST_DURATION.labels(request.method, path).observe(perf_counter() - started)
        return response

    @app.get("/healthz", tags=["runtime"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["runtime"])
    def readyz() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/api/v1/status", tags=["incident"])
    def incident_status() -> dict[str, object]:
        before = service.status()
        incident = service.detect_failure()
        if incident is None:
            metrics.ACTIVE_INCIDENT.set(0)
            return before
        previous_incident = before["incident"]
        was_detected = (
            isinstance(previous_incident, dict)
            and previous_incident["detected_at"] is not None
        )
        if incident.detected_at is not None and not was_detected and incident.active:
            metrics.INCIDENT_EVENTS.labels("detected").inc()
        metrics.ACTIVE_INCIDENT.set(1 if incident.active else 0)
        return service.status()

    @app.post("/api/v1/failure", tags=["incident"])
    def set_failure(request: FailureRequest) -> dict[str, object]:
        if request.enabled:
            incident = service.start_failure(request.reason)
            metrics.INCIDENT_EVENTS.labels("opened").inc()
            metrics.ACTIVE_INCIDENT.set(1)
            return {"active": True, "reason": incident.reason, "opened_at": incident.opened_at}

        incident = service.recover_failure()
        metrics.INCIDENT_EVENTS.labels("recovered").inc()
        metrics.ACTIVE_INCIDENT.set(0)
        return {"active": False, "recovered_at": incident.recovered_at if incident else None}

    @app.get("/api/v1/checkout", tags=["workload"])
    def checkout() -> dict[str, str]:
        try:
            return service.checkout()
        except ControlledFailure as failure:
            metrics.CONTROLLED_FAILURES.labels(failure.reason).inc()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "controlled_failure", "reason": failure.reason},
                headers={"Retry-After": "1"},
            ) from failure

    @app.get("/metrics", include_in_schema=False)
    def prometheus_metrics() -> Response:
        payload, content_type = metrics.exposition()
        return Response(content=payload, media_type=content_type)

    return app


app = create_app()
