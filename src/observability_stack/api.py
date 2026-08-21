"""FastAPI adapter for a three-signal observable checkout demo."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from time import monotonic, perf_counter
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from .application import ObservationService
from .domain import ControlledFailure
from .infrastructure.metrics import Metrics
from .infrastructure.store import InMemoryIncidentStore
from .infrastructure.telemetry import Telemetry, current_trace_id


class FailureRequest(BaseModel):
    enabled: bool = Field(description="Enable or disable the controlled failure.")
    incident_id: str | None = Field(default=None, min_length=8, max_length=80)
    reason: str = Field(default="dependency_timeout", min_length=3, max_length=80)


def create_app(otlp_endpoint: str | None = None) -> FastAPI:
    service = ObservationService(InMemoryIncidentStore(), monotonic)
    metrics = Metrics()
    telemetry = Telemetry(
        "observability-stack",
        otlp_endpoint if otlp_endpoint is not None else os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        telemetry.shutdown()

    app = FastAPI(
        title="#25 Observability Stack",
        version="2.0.0",
        description="Local-first metrics, traces and logs around a controlled incident.",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def observe_http(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started = perf_counter()
        path = request.url.path
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        with telemetry.start_server_span(f"{request.method} {path}") as span:
            span.set_attribute("http.request.method", request.method)
            span.set_attribute("url.path", path)
            span.set_attribute("correlation.id", correlation_id)
            try:
                response = await call_next(request)
            except Exception as error:
                telemetry.mark_error(error)
                metrics.observe_request(request.method, path, 500, perf_counter() - started)
                raise
            span.set_attribute("http.response.status_code", response.status_code)
            metrics.observe_request(
                request.method, path, response.status_code, perf_counter() - started
            )
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Trace-ID"] = current_trace_id()
            return response

    @app.get("/healthz", tags=["runtime"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["runtime"])
    async def readyz() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/api/v1/status", tags=["incident"])
    async def incident_status(request: Request) -> dict[str, object]:
        before = service.status()
        incident = service.detect_failure()
        if incident is None:
            metrics.active_incident.set(0)
            return before
        previous = before["incident"]
        was_detected = isinstance(previous, dict) and previous["detected_at"] is not None
        if incident.detected_at is not None and not was_detected and incident.active:
            trace_id = telemetry.lifecycle_event(
                "detected",
                incident.incident_id,
                incident.reason,
                request.headers.get("X-Correlation-ID", incident.incident_id),
            )
            metrics.record_event("detected", incident.incident_id, trace_id)
        metrics.active_incident.set(1 if incident.active else 0)
        return service.status()

    @app.post("/api/v1/failure", tags=["incident"])
    async def set_failure(request: FailureRequest, http_request: Request) -> dict[str, object]:
        correlation_id = http_request.headers.get("X-Correlation-ID", request.incident_id or "")
        if request.enabled:
            incident = service.start_failure(request.incident_id or str(uuid4()), request.reason)
            trace_id = telemetry.lifecycle_event(
                "opened",
                incident.incident_id,
                incident.reason,
                correlation_id or incident.incident_id,
            )
            metrics.record_event("opened", incident.incident_id, trace_id)
            metrics.active_incident.set(1)
            return {"active": True, "incident": service.status()["incident"]}

        incident = service.recover_failure()
        if incident is not None:
            trace_id = telemetry.lifecycle_event(
                "recovered",
                incident.incident_id,
                incident.reason,
                correlation_id or incident.incident_id,
            )
            metrics.record_event("recovered", incident.incident_id, trace_id)
        metrics.active_incident.set(0)
        return {"active": False, "incident": service.status()["incident"]}

    @app.get("/api/v1/checkout", tags=["workload"])
    async def checkout() -> dict[str, str]:
        try:
            return service.checkout()
        except ControlledFailure as failure:
            trace_id = current_trace_id()
            metrics.record_failure(failure.reason, failure.incident_id, trace_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "controlled_failure",
                    "incident_id": failure.incident_id,
                    "reason": failure.reason,
                },
                headers={"Retry-After": "1"},
            ) from failure

    @app.get("/metrics", include_in_schema=False)
    async def prometheus_metrics() -> Response:
        payload, content_type = metrics.exposition()
        return Response(content=payload, headers={"Content-Type": content_type})

    return app


app = create_app()
