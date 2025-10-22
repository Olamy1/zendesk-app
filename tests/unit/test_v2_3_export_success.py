from fastapi.testclient import TestClient
from backend.main import app


def test_v2_3_export_success(monkeypatch):
    import backend.services.zendesk_service as zs
    import backend.utils.helpers as helpers
    import backend.services.sharepoint_service as sp
    import backend.services.email_service as mail

    def _search(group_ids=None, statuses=None):
        return [{"id": 1, "status": "open", "updated_at": "t"}]

    def _status_map(tickets):
        return {1: {"status": "open", "updated_at": "t"}}

    def _enrich(m):
        return None

    def _win():
        return {"start": "s", "end": "e"}

    def _rows(tickets, status_map, win, bucketed=True):
        return [{"id": 1}]

    def _wb(rows):
        return (b"bytes", "export.xlsx")

    def _upload(filename, content):
        return "https://sharepoint/site/export.xlsx"

    def _email(url, name):
        return None

    monkeypatch.setattr(zs, "search_by_groups_and_statuses", _search)
    monkeypatch.setattr(zs, "build_status_map", _status_map)
    monkeypatch.setattr(zs, "enrich_with_resolution_times", _enrich)
    monkeypatch.setattr(helpers, "compute_meeting_window", _win)
    monkeypatch.setattr(helpers, "build_ticket_rows", _rows)
    monkeypatch.setattr(helpers, "make_ticket_workbook", _wb)
    monkeypatch.setattr(sp, "upload_bytes", _upload)
    monkeypatch.setattr(mail, "send_directors_export_link", _email)

    monkeypatch.setenv("API_AUTH_TOKEN", "t")
    client = TestClient(app)
    r = client.post(
        "/api/v2/tickets/export?group_ids=1&statuses=open",
        headers={"Authorization": "Bearer t"},
    )
    j = r.json()
    assert r.status_code == 200
    assert j["ok"] is True
    assert j["filename"] == "export.xlsx"
    assert j["sharepointUrl"].startswith("https://")
