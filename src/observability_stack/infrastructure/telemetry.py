"""Explicit OpenTelemetry and structured-logging adapter."""

from __future__ import annotations

import json
import logging
from contextlib import AbstractContextManager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import Span, SpanKind, Status, StatusCode, Tracer


def current_trace_id() -> str:
    context = trace.get_current_span().get_span_context()
    return format(context.trace_id, "032x") if context.is_valid else "0" * 32


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "trace_id": current_trace_id(),
        }
        for name in ("event_name", "incident_id", "reason", "correlation_id"):
            value = getattr(record, name, None)
            if value is not None:
                payload[name] = value
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


class Telemetry:
    """Application-owned providers; no global provider mutation is required."""

    def __init__(self, service_name: str, otlp_endpoint: str | None = None) -> None:
        resource = Resource.create({"service.name": service_name})
        self._tracer_provider = TracerProvider(resource=resource)
        self._logger_provider = LoggerProvider(resource=resource)
        if otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            endpoint = otlp_endpoint.rstrip("/")
            self._tracer_provider.add_span_processor(
                SimpleSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces"))
            )
            self._logger_provider.add_log_record_processor(
                SimpleLogRecordProcessor(OTLPLogExporter(endpoint=f"{endpoint}/v1/logs"))
            )
        self.tracer: Tracer = self._tracer_provider.get_tracer(service_name)
        self.logger = logging.getLogger(f"{service_name}.{id(self)}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        stream = logging.StreamHandler()
        stream.setFormatter(JsonFormatter())
        self.logger.addHandler(stream)
        if otlp_endpoint:
            self.logger.addHandler(LoggingHandler(logger_provider=self._logger_provider))

    def lifecycle_event(
        self, event: str, incident_id: str, reason: str, correlation_id: str
    ) -> str:
        with self.tracer.start_as_current_span(f"incident.{event}") as span:
            span.set_attribute("incident.id", incident_id)
            span.set_attribute("incident.event", event)
            span.set_attribute("incident.reason", reason)
            span.set_attribute("correlation.id", correlation_id)
            self.logger.info(
                "incident.lifecycle",
                extra={
                    "event_name": event,
                    "incident_id": incident_id,
                    "reason": reason,
                    "correlation_id": correlation_id,
                },
            )
            return current_trace_id()

    def start_server_span(self, name: str) -> AbstractContextManager[Span]:
        return self.tracer.start_as_current_span(name, kind=SpanKind.SERVER)

    @staticmethod
    def mark_error(error: BaseException) -> None:
        span = trace.get_current_span()
        span.record_exception(error)
        span.set_status(Status(StatusCode.ERROR, str(error)))

    def shutdown(self) -> None:
        self._logger_provider.shutdown()
        self._tracer_provider.shutdown()
        for handler in list(self.logger.handlers):
            handler.close()
            self.logger.removeHandler(handler)
