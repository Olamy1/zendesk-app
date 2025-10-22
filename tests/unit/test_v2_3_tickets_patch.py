from fastapi.testclient import TestClient
from backend.main import app


def test_v2_3_patch_ticket_status(monkeypatch):
    import backend.services.zendesk_service as zs

    def _update(ticket_id: int, **fields):
        return {"id": ticket_id, **fields}

    monkeypatch.setattr(zs, "update_ticket", _update)
    monkeypatch.setenv("API_AUTH_TOKEN", "t")
    client = TestClient(app)
    r = client.patch(
        "/api/v2/tickets/123",
        headers={"Authorization": "Bearer t"},
        json={"status": "open"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["ticket"]["status"] == "open"


def test_v2_3_patch_ticket_assignee_group(monkeypatch):
    import backend.services.zendesk_service as zs

    def _get_user(uid: int):
        return {"id": uid, "group_id": 77}

    def _update(ticket_id: int, **fields):
        return {"id": ticket_id, **fields}

    monkeypatch.setattr(zs, "get_user", _get_user)
    monkeypatch.setattr(zs, "update_ticket", _update)
    monkeypatch.setenv("API_AUTH_TOKEN", "t")
    client = TestClient(app)
    r = client.patch(
        "/api/v2/tickets/222",
        headers={"Authorization": "Bearer t"},
        json={"assignee_id": 555},
    )
    assert r.status_code == 200
    body = r.json()["ticket"]
    assert body["assignee_id"] == 555
    assert body["group_id"] == 77
