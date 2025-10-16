# =================================================================================================
# File: tests/unit/test_tickets.py
# Description:
#   Unit tests for OAPS Zendesk App — Tickets router logic only.
#
# Purpose:
#   Validate logical outcomes (status codes, JSON shapes, and local processing)
#   while mocking all external dependencies (Zendesk, SharePoint, Email).
#
# Author: Olivier Lamy
# Version: 2.2.0 | October 2025
# =================================================================================================

import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


# -------------------------------------------------------------------------------------------------
# PATCH /api/tickets/{ticket_id}
# -------------------------------------------------------------------------------------------------
def test_patch_ticket_zendesk_error(monkeypatch):
    """
    Router wraps Zendesk update failures as 400 (client/upstream request issue)
    per current implementation.
    """
    def mock_update_ticket(*a, **kw):
        raise Exception("API down")

    monkeypatch.setattr("backend.services.zendesk_service.update_ticket", mock_update_ticket)
    resp = client.patch("/api/tickets/123", json={"status": "open"})
    assert resp.status_code == 400
    assert "Zendesk update failed" in resp.json()["detail"]


def test_patch_ticket_noop(monkeypatch):
    """No fields -> router returns ok/noop=True without calling Zendesk."""
    monkeypatch.setattr("backend.services.zendesk_service.update_ticket", lambda *a, **kw: {"id": 123})
    resp = client.patch("/api/tickets/123", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("ok") is True and body.get("noop") is True


# -------------------------------------------------------------------------------------------------
# GET /api/tickets/tickets (normalization)
# -------------------------------------------------------------------------------------------------
def test_get_tickets_with_filters(monkeypatch):
    """GET /tickets with filters should return normalized rows."""
    def mock_search_by_groups_and_statuses(*a, **kw):
        return [{"id": 1, "status": "open", "subject": "Test", "created_at": "2025-09-01T12:00:00"}]

    monkeypatch.setattr(
        "backend.services.zendesk_service.search_by_groups_and_statuses",
        mock_search_by_groups_and_statuses,
    )
    monkeypatch.setattr("backend.services.zendesk_service.build_status_map", lambda t: {1: {"status": "open"}})
    monkeypatch.setattr("backend.services.zendesk_service.enrich_with_resolution_times", lambda sm: None)

    resp = client.get("/api/tickets/tickets?group_ids=1&statuses=open")
    assert resp.status_code == 200
    data = resp.json()
    assert "rows" in data
    assert isinstance(data["rows"], list)


# -------------------------------------------------------------------------------------------------
# GET /api/tickets/meeting-window
# -------------------------------------------------------------------------------------------------
def test_get_meeting_window(monkeypatch):
    """Mock compute_meeting_window for deterministic values."""
    monkeypatch.setattr(
        "backend.routers.tickets.compute_meeting_window",
        lambda: {"start": "2025-09-01", "end": "2025-09-15"},
    )
    resp = client.get("/api/tickets/meeting-window")
    assert resp.status_code == 200
    data = resp.json()
    assert data["start"] == "2025-09-01"
    assert data["end"] == "2025-09-15"


# -------------------------------------------------------------------------------------------------
# POST /api/tickets/{ticket_id}/comments
# -------------------------------------------------------------------------------------------------
def test_post_comment_success(monkeypatch):
    """POST comment should succeed with valid payload."""
    def mock_add_comment(ticket_id, text, public=False):
        return {"id": ticket_id, "comment": text, "public": public}

    # ✅ patch the correct service function
    monkeypatch.setattr("backend.services.zendesk_service.add_comment", mock_add_comment)

    resp = client.post("/api/tickets/321/comments", json={"body": "Test comment", "is_public": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["ticket"]["comment"] == "Test comment"
    assert body["ticket"]["public"] is True


def test_post_comment_empty(monkeypatch):
    """
    Send is_public to pass Pydantic validation (avoid 422).
    Router rejects empty body with 400.
    """
    def mock_add_comment(ticket_id, text, public=False):
        # Won't be reached because router raises 400 before calling service
        return {"id": ticket_id, "comment": text, "public": public}

    monkeypatch.setattr("backend.services.zendesk_service.add_comment", mock_add_comment)
    resp = client.post("/api/tickets/123/comments", json={"body": "", "is_public": False})
    assert resp.status_code == 400
    assert "Empty comment" in resp.text


def test_post_comment_zendesk_failure(monkeypatch):
    os.environ["UNIT_MODE"] = "0"  # ✅ ensure we don't skip zendesk logic

    def mock_add_comment(*a, **kw):
        raise Exception("Zendesk unavailable")

    monkeypatch.setattr("backend.services.zendesk_service.add_comment", mock_add_comment)
    resp = client.post("/api/tickets/123/comments", json={"body": "Hello", "is_public": False})
    assert resp.status_code == 400
    assert "Zendesk comment failed" in resp.text


# -------------------------------------------------------------------------------------------------
# POST /api/tickets/export — Export + Email flow (SharePoint + Email mocked)
# -------------------------------------------------------------------------------------------------
def test_export_and_email_success(monkeypatch):
    """Happy path for export — mock dataset, workbook, SP upload, and email."""
    # dataset
    monkeypatch.setattr(
        "backend.services.zendesk_service.search_by_groups_and_statuses",
        lambda *a, **k: [{"id": 1, "status": "open", "subject": "Test", "created_at": "2025-09-01T00:00:00"}],
    )
    # build status map + enrich
    monkeypatch.setattr("backend.services.zendesk_service.build_status_map", lambda t: {1: {"status": "open"}})
    monkeypatch.setattr("backend.services.zendesk_service.enrich_with_resolution_times", lambda sm: None)
    # workbook
    monkeypatch.setattr(
        "backend.utils.helpers.make_ticket_workbook",
        lambda rows: (b"bytes", "unit-export.xlsx"),
    )
    # SharePoint upload + email
    monkeypatch.setattr(
        "backend.services.sharepoint_service.upload_bytes",
        lambda name, data: "https://sharepoint.example.com/unit-export.xlsx",
    )
    monkeypatch.setattr(
        "backend.services.email_service.send_directors_export_link",
        lambda url, name: True,
    )

    resp = client.post("/api/tickets/export")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["sharepointUrl"].startswith("https://sharepoint.example.com/")


def test_export_and_email_sharepoint_fail(monkeypatch):
    """SharePoint failure mapped to 502 per route code."""
    # dataset + workbook as above
    monkeypatch.setattr(
        "backend.services.zendesk_service.search_by_groups_and_statuses",
        lambda *a, **k: [{"id": 1, "status": "open", "subject": "Test"}],
    )
    monkeypatch.setattr("backend.services.zendesk_service.build_status_map", lambda t: {1: {"status": "open"}})
    monkeypatch.setattr("backend.services.zendesk_service.enrich_with_resolution_times", lambda sm: None)
    monkeypatch.setattr(
        "backend.utils.helpers.make_ticket_workbook",
        lambda rows: (b"bytes", "unit-export.xlsx"),
    )

    def mock_upload_bytes(name, data):
        raise Exception("SharePoint service error")

    monkeypatch.setattr("backend.services.sharepoint_service.upload_bytes", mock_upload_bytes)
    monkeypatch.setattr(
        "backend.services.email_service.send_directors_export_link",
        lambda url, name: True,
    )

    resp = client.post("/api/tickets/export")
    assert resp.status_code == 502
    assert "SharePoint upload failed" in resp.text


def test_export_and_email_email_fail(monkeypatch):
    """Email failure mapped to 502 per route code."""
    # dataset + workbook + SP upload OK
    monkeypatch.setattr(
        "backend.services.zendesk_service.search_by_groups_and_statuses",
        lambda *a, **k: [{"id": 1, "status": "open", "subject": "Test"}],
    )
    monkeypatch.setattr("backend.services.zendesk_service.build_status_map", lambda t: {1: {"status": "open"}})
    monkeypatch.setattr("backend.services.zendesk_service.enrich_with_resolution_times", lambda sm: None)
    monkeypatch.setattr(
        "backend.utils.helpers.make_ticket_workbook",
        lambda rows: (b"bytes", "unit-export.xlsx"),
    )
    monkeypatch.setattr(
        "backend.services.sharepoint_service.upload_bytes",
        lambda name, data: "https://sharepoint.example.com/unit-export.xlsx",
    )

    def mock_email(url, name):
        raise Exception("Email service error")

    monkeypatch.setattr("backend.services.email_service.send_directors_export_link", mock_email)

    resp = client.post("/api/tickets/export")
    assert resp.status_code == 502
    assert "Email send failed" in resp.text