# =====================================================================
# File: tests/unit/test_users.py
# =====================================================================

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_list_users_success(monkeypatch):
    def mock_list_users():
        return [{"id": 1, "name": "Test User"}]

    # Patch the zd object inside users.py
    monkeypatch.setattr("backend.routers.users.zd", type("ZD", (), {"list_oaps_users": mock_list_users}))

    resp = client.get("/api/users")
    assert resp.status_code == 200
    assert resp.json() == {"users": [{"id": 1, "name": "Test User"}]}


def test_list_users_failure(monkeypatch):
    def mock_list_users():
        raise Exception("Boom")

    monkeypatch.setattr("backend.routers.users.zd", type("ZD", (), {"list_oaps_users": mock_list_users}))

    resp = client.get("/api/users")
    assert resp.status_code == 502
    assert "User fetch failed" in resp.json()["detail"]
