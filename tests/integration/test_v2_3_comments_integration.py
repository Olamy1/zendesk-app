# Phase 3 integration-ish check for comments endpoint using monkeypatch

from fastapi.testclient import TestClient
from backend.main import app


def test_v2_3_comments_endpoint_works_with_stub(monkeypatch):
    # Ensure middleware accepts the test token in integration mode
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")
    def _stub(ticket_id: int, limit: int = 3):
        return [{"id": 1, "author_id": 10, "public": True, "created_at": "t", "body": "ok"}]

    import backend.services.zendesk_service as zs
    monkeypatch.setattr(zs, "get_last_comments", _stub)

    client = TestClient(app)
    r = client.get(
        "/api/v2/tickets/555/comments?limit=1",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("ok") is True
    assert payload.get("comments", [{}])[0].get("body") == "ok"
