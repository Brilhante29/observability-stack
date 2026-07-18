"""Prometheus adapter kept outside the application policy."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUESTS = Counter(
    "observability_http_requests_total",
    "HTTP requests handled by the demo service.",
    ("method", "path", "status"),
)
REQUEST_DURATION = Histogram(
    "observability_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "path"),
)
CONTROLLED_FAILURES = Counter(
    "observability_controlled_failures_total",
    "Requests rejected by the intentional failure scenario.",
    ("reason",),
)
INCIDENT_EVENTS = Counter(
    "observability_incident_events_total",
    "Incident lifecycle events emitted by the demo.",
    ("event",),
)
ACTIVE_INCIDENT = Gauge(
    "observability_active_incident",
    "1 when the controlled incident is active, otherwise 0.",
)


def exposition() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
