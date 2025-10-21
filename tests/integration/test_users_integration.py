# =================================================================================================
# Integration Tests — Users Router
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

def auth_headers():
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.integration
def test_list_users_success(monkeypatch):
    import backend.routers.users as users

    def _mock_list():
        # Your users router normalizes to id + name for zd.list_oaps_users result
        return [{"id": 1, "name": "Test User"}]

    # Your router prefers zd.list_oaps_users when present
    monkeypatch.setattr(users.zd, "list_oaps_users", _mock_list)

    resp = client.get("/api/users/", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data and isinstance(data["users"], list)
    assert data["users"][0]["name"] == "Test User"

@pytest.mark.integration
def test_list_users_failure(monkeypatch):
    import backend.routers.users as users
    from fastapi import HTTPException

    def _fail_list():
        raise Exception("Zendesk service error")

    monkeypatch.setattr(users.zd, "list_oaps_users", _fail_list)

    resp = client.get("/api/users/", headers=auth_headers())
    # Your router catches Exception and raises HTTPException(502, ...)
    assert resp.status_code == 502
    assert "User fetch failed" in resp.text

@pytest.mark.integration
def test_list_users_empty(monkeypatch):
    import backend.routers.users as users
    monkeypatch.setattr(users.zd, "list_oaps_users", lambda: [])

    resp = client.get("/api/users/", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data and data["users"] == []
