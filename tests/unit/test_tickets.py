# =====================================================================
# File: tests/unit/test_tickets.py
# Description: Unit tests for tickets.py routes
# =====================================================================

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_meeting_window(monkeypatch):
    """Should return mocked meeting window"""
    monkeypatch.setattr(
        "backend.routers.tickets.compute_meeting_window",
        lambda: {"start": "2025-09-01", "end": "2025-09-15"},
    )
    # ✅ Corrected path
    resp = client.get("/api/tickets/meeting-window")
    assert resp.status_code == 200
    data = resp.json()
    assert "start" in data and "end" in data


def test_patch_ticket(monkeypatch):
    """PATCH ticket should call zendesk_service.update_ticket"""

    def mock_update_ticket(ticket_id, **fields):
        return {"id": ticket_id, **fields}

    monkeypatch.setattr(
        "backend.services.zendesk_service.update_ticket",
        mock_update_ticket,
    )

    # ✅ Corrected path
    resp = client.patch("/api/tickets/123", json={"status": "open"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["ticket"]["status"] == "open"


def test_get_tickets_with_filters(monkeypatch):
    """GET /tickets with filters should return rows"""

    def mock_search(*args, **kwargs):
        return [{"id": 1, "status": "open", "subject": "Test", "created_at": "2025-09-01T12:00:00"}]

    monkeypatch.setattr("backend.services.zendesk_service.search_by_groups_and_statuses", mock_search)
    monkeypatch.setattr("backend.services.zendesk_service.build_status_map", lambda t: {1: {"status": "open"}})
    monkeypatch.setattr("backend.services.zendesk_service.enrich_with_resolution_times", lambda sm: None)

    resp = client.get("/api/tickets/tickets?group_ids=1&statuses=open")
    assert resp.status_code == 200
    data = resp.json()
    assert "rows" in data


def test_post_comment_success(monkeypatch):
    """POST comment should succeed"""

    def mock_add_comment(ticket_id, text, public=False):
        return {"id": ticket_id, "comment": text, "public": public}

    monkeypatch.setattr("backend.services.zendesk_service.add_comment", mock_add_comment)

    resp = client.post("/api/tickets/123/comments", json={"body": "Hello", "public": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["ticket"]["comment"] == "Hello"


def test_post_comment_empty_body():
    """POST comment with empty body should fail"""
    resp = client.post("/api/tickets/123/comments", json={"body": ""})
    assert resp.status_code == 400
