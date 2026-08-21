import unittest

from fastapi.testclient import TestClient

from observability_stack.api import create_app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = TestClient(create_app(otlp_endpoint=""))
        self.client = self.context.__enter__()

    def tearDown(self) -> None:
        self.context.__exit__(None, None, None)

    def test_runtime_and_workload_endpoints(self) -> None:
        self.assertEqual(self.client.get("/healthz").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/readyz").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/checkout").status_code, 200)
        self.assertEqual(
            self.client.get("/api/v1/status").json(),
            {"active": False, "incident": None},
        )

    def test_controlled_failure_is_visible_and_recoverable(self) -> None:
        response = self.client.post(
            "/api/v1/failure",
            headers={"X-Correlation-ID": "incident-api-001"},
            json={
                "enabled": True,
                "incident_id": "incident-api-001",
                "reason": "dependency_timeout",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["incident"]["incident_id"], "incident-api-001")
        self.assertEqual(len(response.headers["X-Trace-ID"]), 32)
        self.assertEqual(self.client.get("/api/v1/checkout").status_code, 503)
        self.assertTrue(self.client.get("/api/v1/status").json()["active"])

        response = self.client.post(
            "/api/v1/failure",
            headers={"X-Correlation-ID": "incident-api-001"},
            json={"enabled": False, "incident_id": "incident-api-001"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/checkout").status_code, 200)

    def test_metrics_endpoint_exposes_prometheus_samples(self) -> None:
        self.client.get("/api/v1/checkout")
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("observability_http_requests_total", response.text)
        self.assertIn("observability_http_request_duration_seconds", response.text)

    def test_lifecycle_metrics_carry_incident_and_trace_exemplars(self) -> None:
        incident_id = "incident-api-002"
        headers = {"X-Correlation-ID": incident_id}
        opened = self.client.post(
            "/api/v1/failure",
            headers=headers,
            json={"enabled": True, "incident_id": incident_id},
        )
        self.client.get("/api/v1/status", headers=headers)
        recovered = self.client.post(
            "/api/v1/failure",
            headers=headers,
            json={"enabled": False, "incident_id": incident_id},
        )
        metrics = self.client.get("/metrics").text
        self.assertIn(incident_id, metrics)
        self.assertIn(opened.headers["X-Trace-ID"], metrics)
        self.assertIn(recovered.headers["X-Trace-ID"], metrics)
