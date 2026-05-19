"""Smoke test: the FastAPI app boots and `/api/v1/health` returns ok.

Replaced in Phase 1.3 with a real health check that probes DB, Redis, and the
last successful LLM call.
"""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    """The Phase 0 stub health endpoint returns 200 + status=ok."""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
