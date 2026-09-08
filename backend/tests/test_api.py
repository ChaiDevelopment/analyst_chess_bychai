from fastapi.testclient import TestClient
import pytest

from app.config import settings
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "engine_available" in body


@pytest.mark.skipif(
    not settings.engine_available,
    reason="Stockfish is required for engine integration tests",
)
def test_analyze_endpoint_success(sample_pgn):
    resp = client.post("/api/analyze", json={"pgn": sample_pgn, "depth": 8})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["moves"]) == 10
    assert "summary" in body
    assert body["game"]["white"] == "Player"


def test_analyze_endpoint_invalid_pgn():
    resp = client.post("/api/analyze", json={"pgn": "not a real pgn"})
    assert resp.status_code == 400
    assert "Invalid PGN" in resp.json()["detail"] or "detail" in resp.json()


def test_analyze_endpoint_empty_pgn():
    resp = client.post("/api/analyze", json={"pgn": ""})
    # empty string fails pydantic min_length validation -> 422
    assert resp.status_code == 422


def test_analyze_endpoint_missing_field():
    resp = client.post("/api/analyze", json={})
    assert resp.status_code == 422
