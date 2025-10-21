# =================================================================================================
# Integration Tests — Security Middleware
# =================================================================================================
import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app as base_app
from backend.config import get_settings

# Ensure integration env + token is set BEFORE client creation
os.environ["APP_ENV"] = "integration"
os.environ["UNIT_MODE"] = "0"
os.environ["INTEGRATION_MODE"] = "1"

settings = get_settings()
token = settings.ZENDESK_API_TOKEN or "valid-token"
os.environ["ZENDESK_API_TOKEN"] = token  # ✅ middleware compares to this

client = TestClient(base_app)

@pytest.mark.integration
def test_token_missing_rejects_request():
    # ⚠️ Your tickets "list" endpoint is /api/tickets/tickets (not /api/tickets)
    resp = client.get("/api/tickets/tickets")
    assert resp.status_code == 401
    assert "Missing Authorization" in resp.text

@pytest.mark.integration
def test_token_invalid_rejects_request():
    resp = client.get("/api/tickets/tickets", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 403
    assert "Invalid" in resp.text

@pytest.mark.integration
def test_token_valid_allows_request():
    resp = client.get("/api/tickets/tickets", headers={"Authorization": f"Bearer {token}"})
    # Depending on data, 200 or 204 is fine for "list" style endpoints
    assert resp.status_code in (200, 204)

@pytest.mark.integration
def test_docs_routes_are_open():
    for path in ["/", "/docs", "/redoc", "/openapi.json"]:
        r = client.get(path)
        assert r.status_code in (200, 404)
