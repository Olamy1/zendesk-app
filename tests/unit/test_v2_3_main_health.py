from fastapi.testclient import TestClient
from backend.main import app


def test_v2_3_health_root():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_v2_3_health_endpoints(monkeypatch):
    client = TestClient(app)
    # /health is public
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

    # versioned health requires auth
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")
    r2 = client.get("/api/v2/health", headers={"Authorization": "Bearer test-token"})
    assert r2.status_code == 200
    assert r2.json().get("status") == "ok"
