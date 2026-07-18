import unittest

from fastapi.testclient import TestClient

from observability_stack.api import create_app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def test_runtime_and_workload_endpoints(self) -> None:
        self.assertEqual(self.client.get("/healthz").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/readyz").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/checkout").status_code, 200)

    def test_controlled_failure_is_visible_and_recoverable(self) -> None:
        response = self.client.post(
            "/api/v1/failure", json={"enabled": True, "reason": "dependency_timeout"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/checkout").status_code, 503)
        self.assertTrue(self.client.get("/api/v1/status").json()["active"])

        response = self.client.post("/api/v1/failure", json={"enabled": False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/checkout").status_code, 200)

    def test_metrics_endpoint_exposes_prometheus_samples(self) -> None:
        self.client.get("/api/v1/checkout")
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("observability_http_requests_total", response.text)
        self.assertIn("observability_http_request_duration_seconds", response.text)
