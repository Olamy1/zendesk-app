from fastapi.testclient import TestClient
from backend.main import app


def test_v2_3_users_happy_path(monkeypatch):
    import backend.services.zendesk_service as zs

    def _stub():
        return [{"id": 1, "name": "Alice", "group_id": 10}, {"id": 2, "name": "Bob"}]

    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")
    monkeypatch.setattr(zs, "list_oaps_users", _stub)
    client = TestClient(app)
    r = client.get("/api/v2/users", headers={"Authorization": "Bearer test-token"})
    assert r.status_code == 200
    data = r.json()["users"]
    assert {u["name"] for u in data} == {"Alice", "Bob"}


def test_v2_3_users_error(monkeypatch):
    import backend.services.zendesk_service as zs

    def _boom():
        raise RuntimeError("fail")

    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")
    monkeypatch.setattr(zs, "list_oaps_users", _boom)
    client = TestClient(app)
    r = client.get("/api/v2/users", headers={"Authorization": "Bearer test-token"})
    assert r.status_code == 502
    assert "User fetch failed" in r.json()["detail"]
