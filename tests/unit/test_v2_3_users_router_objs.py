from types import SimpleNamespace
from fastapi.testclient import TestClient
from backend.main import app


def test_v2_3_users_object_items(monkeypatch):
    import backend.services.zendesk_service as zs

    def _stub():
        return [SimpleNamespace(id=11, name="Jane"), SimpleNamespace(id=22, name="John")]

    monkeypatch.setenv("API_AUTH_TOKEN", "tok")
    monkeypatch.setattr(zs, "list_oaps_users", _stub)
    client = TestClient(app)
    r = client.get("/api/v2/users", headers={"Authorization": "Bearer tok"})
    assert r.status_code == 200
    names = {u["name"] for u in r.json()["users"]}
    assert names == {"Jane", "John"}

