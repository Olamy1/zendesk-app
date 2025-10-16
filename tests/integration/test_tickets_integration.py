# =================================================================================================
# Integration Tests — Tickets Router
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
def test_get_tickets_with_filters(monkeypatch):
    resp = client.get("/api/tickets?status=open", headers=auth_headers())
    assert resp.status_code in (200, 204)
    if resp.status_code == 200:
        body = resp.json()
        assert isinstance(body, dict)
        assert "tickets" in body


@pytest.mark.integration
def test_patch_ticket_valid(monkeypatch):
    payload = {"status": "solved"}
    resp = client.patch("/api/tickets/123", json=payload, headers=auth_headers())
    assert resp.status_code in (200, 204)
    if resp.status_code == 200:
        assert resp.json().get("status") == "solved"


@pytest.mark.integration
def test_patch_ticket_invalid_payload():
    resp = client.patch("/api/tickets/123", json={"invalid": True}, headers=auth_headers())
    assert resp.status_code in (400, 422)


@pytest.mark.integration
def test_patch_ticket_zendesk_error(monkeypatch):
    # Simulate Zendesk API error (monkeypatch to raise)
    from backend.routers import tickets

    async def mock_update_ticket(*a, **kw):
        from fastapi import HTTPException
        raise HTTPException(status_code=502, detail="Zendesk service unavailable")

    monkeypatch.setattr(tickets, "update_ticket", mock_update_ticket)
    resp = client.patch("/api/tickets/999", json={"status": "open"}, headers=auth_headers())
    assert resp.status_code == 502


@pytest.mark.integration
def test_post_comment_success():
    payload = {"body": "This is an integration test comment"}
    resp = client.post("/api/tickets/456/comments", json=payload, headers=auth_headers())
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert "body" in data or "comment" in data


@pytest.mark.integration
def test_post_comment_empty_body():
    resp = client.post("/api/tickets/456/comments", json={}, headers=auth_headers())
    assert resp.status_code == 422
