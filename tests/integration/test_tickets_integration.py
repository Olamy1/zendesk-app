# =================================================================================================
# Integration Tests — Tickets Router
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
def test_get_tickets_with_filters():
    # ✅ Correct route: /api/tickets/tickets
    resp = client.get("/api/tickets/tickets?statuses=open", headers=auth_headers())
    assert resp.status_code in (200, 204)
    if resp.status_code == 200:
        body = resp.json()
        assert isinstance(body, dict)
        # Your handler returns {"rows": [...], "meetingWindow": {...}}
        assert "rows" in body
        assert "meetingWindow" in body

@pytest.mark.integration
def test_patch_ticket_valid(monkeypatch):
    # Your router calls zd.update_ticket (not tickets.update_ticket)
    import backend.routers.tickets as tickets

    def _ok_update(ticket_id, **kw):
        return {"id": ticket_id, "status": kw.get("status", "open"), "updated_at": "2025-10-21T00:00:00Z"}

    monkeypatch.setattr(tickets.zd, "update_ticket", _ok_update)

    payload = {"status": "solved"}
    resp = client.patch("/api/tickets/123", json=payload, headers=auth_headers())
    assert resp.status_code in (200, 204)
    if resp.status_code == 200:
        data = resp.json()
        # Your handler returns {"ok": True, "ticket": {...}}
        assert data["ok"] is True
        assert data["ticket"]["status"] == "solved"

@pytest.mark.integration
def test_patch_ticket_invalid_payload():
    # For invalid payload (no status/assignee_id), your router returns a noop 200
    resp = client.patch("/api/tickets/123", json={"invalid": True}, headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json().get("noop") is True

@pytest.mark.integration
def test_patch_ticket_zendesk_error(monkeypatch):
    import backend.routers.tickets as tickets
    from fastapi import HTTPException

    def _err_update(ticket_id, **kw):
        raise Exception("zendesk service down")

    # The router catches generic Exception and raises HTTPException(status_code=400, ...)
    monkeypatch.setattr(tickets.zd, "update_ticket", _err_update)

    resp = client.patch("/api/tickets/999", json={"status": "open"}, headers=auth_headers())
    assert resp.status_code == 400
    assert "Zendesk update failed" in resp.text

@pytest.mark.integration
def test_post_comment_success(monkeypatch):
    import backend.routers.tickets as tickets

    def _ok_add_comment(ticket_id, text, public=False):
        return {"id": ticket_id, "status": "open", "comment": text, "public": public, "updated_at": "2025-10-21T00:00:00Z"}

    monkeypatch.setattr(tickets.zd, "add_comment", _ok_add_comment)

    # ✅ Schema requires body + is_public (+ optional author_id)
    payload = {"body": "This is an integration test comment", "is_public": True, "author_id": 1}
    resp = client.post("/api/tickets/456/comments", json=payload, headers=auth_headers())
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data["ok"] is True
    assert "ticket" in data
    assert data["ticket"].get("comment") == "This is an integration test comment"

@pytest.mark.integration
def test_post_comment_empty_body():
    # Empty body → 400 per router logic
    payload = {"body": "", "is_public": True}
    resp = client.post("/api/tickets/456/comments", json=payload, headers=auth_headers())
    assert resp.status_code == 400
    assert "Empty comment" in resp.text
