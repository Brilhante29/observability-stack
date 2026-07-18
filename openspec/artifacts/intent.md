# Intent: #25 observability-stack

Build the smallest publishable local application that proves an observable failure lifecycle. The measurable claim is a controlled incident with Prometheus metrics and a deterministic `simulated_mttr_minutes` result of `1.2`.

Non-goals are durable production incident management, real cloud provisioning, distributed load testing and paid credentials. The default path is Docker Compose with API, Prometheus and Grafana on local ports.
