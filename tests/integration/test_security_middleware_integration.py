# =================================================================================================
# Integration Tests — Security Middleware
# =================================================================================================
import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app as base_app
from backend.config import get_settings

os.environ["APP_ENV"] = "integration"
os.environ["UNIT_MODE"] = "0"
os.environ["INTEGRATION_MODE"] = "1"

client = TestClient(base_app)
settings = get_settings()


@pytest.mark.integration
def test_token_missing_rejects_request():
    resp = client.get("/api/tickets")
    assert resp.status_code == 401
    assert "Missing Authorization" in resp.text


@pytest.mark.integration
def test_token_invalid_rejects_request():
    resp = client.get("/api/tickets", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 403
    assert "Invalid" in resp.text


@pytest.mark.integration
def test_token_valid_allows_request(monkeypatch):
    token = settings.ZENDESK_API_TOKEN or "valid-token"
    os.environ["ZENDESK_API_TOKEN"] = token
    resp = client.get("/api/tickets", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (200, 204)  # depends on route behavior


@pytest.mark.integration
def test_docs_routes_are_open():
    for path in ["/", "/docs", "/redoc", "/openapi.json"]:
        r = client.get(path)
        assert r.status_code in (200, 404)
