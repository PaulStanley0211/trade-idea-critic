"""Smoke tests for the Phase 1.2 critique stub endpoints.

These confirm the API shape only. Phase 1.3 introduces full LangGraph wiring
and integration tests with cassettes; these unit tests will keep covering the
HTTP contract.
"""

from fastapi.testclient import TestClient

from app.main import app


def test_post_returns_queued_with_request_id() -> None:
    """POST /api/v1/critique returns 202 with a UUID and status=queued."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/critique",
        json={"thesis": "Long AAPL 195, stop 192, target 201, ORB on 5-min."},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert len(body["request_id"]) == 36  # UUID string form


def test_get_returns_canned_response_for_known_id() -> None:
    """GET /api/v1/critique/{id} returns the canned stub critique."""
    client = TestClient(app)
    post = client.post(
        "/api/v1/critique",
        json={"thesis": "Long AAPL 195, stop 192, target 201, ORB on 5-min."},
    )
    request_id = post.json()["request_id"]
    response = client.get(f"/api/v1/critique/{request_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == request_id
    assert body["status"] == "complete"
    assert body["verdict"] in {"strong", "marginal", "weak"}
    assert "w1.2_stub_response" in body["gap_flags"]


def test_get_unknown_id_returns_404() -> None:
    """Unknown request_id returns 404."""
    client = TestClient(app)
    response = client.get("/api/v1/critique/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_post_validates_thesis_length() -> None:
    """A too-short thesis is rejected by Pydantic validation (422)."""
    client = TestClient(app)
    response = client.post("/api/v1/critique", json={"thesis": "too short"})
    assert response.status_code == 422
