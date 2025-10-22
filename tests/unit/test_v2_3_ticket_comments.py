# Phase 3: Last N comments endpoint tests

from fastapi.testclient import TestClient
from backend.main import app


def test_v2_3_last_comments_happy_path(monkeypatch):
    # Stub service layer
    def _fake_get_last_comments(ticket_id: int, limit: int = 3):
        return [
            {"id": 3, "author_id": 1003, "public": True, "created_at": "2025-10-21T12:03:00Z", "body": "c3"},
            {"id": 2, "author_id": 1002, "public": False, "created_at": "2025-10-21T12:02:00Z", "body": "c2"},
            {"id": 1, "author_id": 1001, "public": True, "created_at": "2025-10-21T12:01:00Z", "body": "c1"},
        ][:limit]

    import backend.services.zendesk_service as zs
    monkeypatch.setattr(zs, "get_last_comments", _fake_get_last_comments)

    client = TestClient(app)
    r = client.get("/api/v2/tickets/123/comments?limit=3")
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("ok") is True
    comments = payload.get("comments", [])
    assert len(comments) == 3
    assert comments[0]["id"] == 3


def test_v2_3_last_comments_error(monkeypatch):
    def _boom(ticket_id: int, limit: int = 3):
        raise RuntimeError("downstream")

    import backend.services.zendesk_service as zs
    monkeypatch.setattr(zs, "get_last_comments", _boom)

    client = TestClient(app)
    r = client.get("/api/v2/tickets/123/comments?limit=2")
    assert r.status_code == 502
    payload = r.json()
    assert "Comments fetch failed" in payload.get("detail", "")
