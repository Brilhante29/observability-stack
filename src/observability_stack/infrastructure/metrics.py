"""Prometheus adapter with an isolated registry per application instance."""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST, generate_latest


class Metrics:
    """Owns bounded demo metrics without leaking global registry state into tests."""

    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.requests = Counter(
            "observability_http_requests_total",
            "HTTP requests handled by the demo service.",
            ("method", "path", "status"),
            registry=self.registry,
        )
        self.request_duration = Histogram(
            "observability_http_request_duration_seconds",
            "HTTP request duration in seconds.",
            ("method", "path"),
            registry=self.registry,
        )
        self.controlled_failures = Counter(
            "observability_controlled_failures_total",
            "Requests rejected by the intentional failure scenario.",
            ("reason", "incident_id"),
            registry=self.registry,
        )
        self.incident_events = Counter(
            "observability_incident_events_total",
            "Incident lifecycle events emitted by the demo.",
            ("event", "incident_id"),
            registry=self.registry,
        )
        self.active_incident = Gauge(
            "observability_active_incident",
            "1 when the controlled incident is active, otherwise 0.",
            registry=self.registry,
        )

    def observe_request(self, method: str, path: str, status: int, duration: float) -> None:
        self.requests.labels(method, path, str(status)).inc()
        self.request_duration.labels(method, path).observe(duration)

    def record_event(self, event: str, incident_id: str, trace_id: str) -> None:
        self.incident_events.labels(event, incident_id).inc(exemplar={"trace_id": trace_id})

    def record_failure(self, reason: str, incident_id: str, trace_id: str) -> None:
        self.controlled_failures.labels(reason, incident_id).inc(
            exemplar={"trace_id": trace_id}
        )

    def exposition(self) -> tuple[bytes, str]:
        payload = generate_latest(self.registry)  # type: ignore[no-untyped-call]
        return payload, CONTENT_TYPE_LATEST
