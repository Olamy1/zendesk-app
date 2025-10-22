from fastapi.testclient import TestClient
from backend.main import app


def test_v2_3_meeting_window_endpoint(monkeypatch):
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")
    client = TestClient(app)
    r = client.get("/api/v2/tickets/meeting-window", headers={"Authorization": "Bearer test-token"})
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_v2_3_get_tickets_ids_csv(monkeypatch):
    # Stub downstream service/helpers to avoid external calls
    import backend.services.zendesk_service as zs
    import backend.utils.helpers as helpers

    def _show_many(ids):
        return [{"id": int(i), "status": "open", "updated_at": "t"} for i in ids]

    def _build_status_map(tickets):
        return {t["id"]: {"status": t["status"], "updated_at": t["updated_at"]} for t in tickets}

    def _enrich(status_map):
        return None

    def _compute_meeting_window():
        return {"start": "s", "end": "e"}

    def _build_rows(tickets, status_map, win, bucketed=True):
        return [{"id": t["id"], "status": status_map[t["id"]]["status"]} for t in tickets]

    monkeypatch.setattr(zs, "show_many", _show_many)
    monkeypatch.setattr(zs, "build_status_map", _build_status_map)
    monkeypatch.setattr(zs, "enrich_with_resolution_times", _enrich)
    monkeypatch.setattr(helpers, "compute_meeting_window", _compute_meeting_window)
    monkeypatch.setattr(helpers, "build_ticket_rows", _build_rows)

    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")
    client = TestClient(app)
    r = client.get(
        "/api/v2/tickets?ids_csv=1,2",
        headers={"Authorization": "Bearer test-token"},
    )
    j = r.json()
    assert r.status_code == 200
    assert len(j["rows"]) == 2
    assert j["rows"][0]["id"] in (1, 2)
