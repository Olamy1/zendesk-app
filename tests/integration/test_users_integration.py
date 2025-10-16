# =================================================================================================
# Integration Tests — Users Router
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
token = settings.ZENDESK_API_TOKEN or "valid-token"


def auth_headers():
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
def test_list_users_success(monkeypatch):
    from backend.routers import users

    async def mock_list_users():
        return [{"id": 1, "name": "Test User", "email": None, "role": "agent", "group_id": 5, "active": True}]

    monkeypatch.setattr(users, "list_users", mock_list_users)
    resp = client.get("/api/users", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    assert isinstance(data["users"], list)
    assert data["users"][0]["name"] == "Test User"


@pytest.mark.integration
def test_list_users_failure(monkeypatch):
    from backend.routers import users
    from fastapi import HTTPException

    async def mock_list_users_fail():
        raise HTTPException(status_code=502, detail="Zendesk service error")

    monkeypatch.setattr(users, "list_users", mock_list_users_fail)
    resp = client.get("/api/users", headers=auth_headers())
    assert resp.status_code == 502
    assert "Zendesk service error" in resp.text


@pytest.mark.integration
def test_list_users_empty(monkeypatch):
    from backend.routers import users

    async def mock_list_users_empty():
        return []

    monkeypatch.setattr(users, "list_users", mock_list_users_empty)
    resp = client.get("/api/users", headers=auth_headers())
    assert resp.status_code in (200, 204)
