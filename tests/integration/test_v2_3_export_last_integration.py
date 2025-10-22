# Phase 3 integration-ish check for last export endpoint

from fastapi.testclient import TestClient
from backend.main import app


def test_v2_3_export_last_default_path(monkeypatch, tmp_path):
    # Point metadata path to a temp file to avoid cross-test interference
    monkeypatch.setenv("EXPORT_META_PATH", str(tmp_path / "export_meta.json"))
    # Ensure middleware accepts the test token in integration mode
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")

    client = TestClient(app)
    resp = client.get(
        "/api/v2/tickets/export/last",
        headers={"Authorization": "Bearer test-token"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
