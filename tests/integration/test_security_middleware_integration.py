# =================================================================================================
# Integration Tests - Security Middleware
# =================================================================================================
import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    # Enforce integration env for each test and disable unit bypass
    monkeypatch.setenv("APP_ENV", "integration")
    monkeypatch.setenv("UNIT_MODE", "0")
    monkeypatch.setenv("INTEGRATION_MODE", "1")

    # Ensure settings reload to pick up env
    from backend import config
    if hasattr(config.get_settings, "cache_clear"):
        config.get_settings.cache_clear()

    # Reload app module after env change
    import backend.main as main_mod
    importlib.reload(main_mod)
    return TestClient(main_mod.app)


@pytest.mark.integration
def test_token_missing_rejects_request(client):
    resp = client.get("/api/tickets/tickets")
    assert resp.status_code == 401
    assert "Missing Authorization" in resp.text


@pytest.mark.integration
def test_token_invalid_rejects_request(client, monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKEN", "valid-token")
    resp = client.get("/api/tickets/tickets", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 403
    assert "Invalid" in resp.text


@pytest.mark.integration
def test_token_valid_allows_request(client, monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKEN", "valid-token")
    resp = client.get("/api/tickets/tickets", headers={"Authorization": "Bearer valid-token"})
    assert resp.status_code in (200, 204)


@pytest.mark.integration
def test_docs_routes_are_open(client):
    for path in ["/", "/docs", "/redoc", "/openapi.json"]:
        r = client.get(path)
        assert r.status_code in (200, 404)

