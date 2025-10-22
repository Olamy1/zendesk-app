# Phase 3: Export metadata endpoint tests

import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app


def test_v2_3_get_last_export_metadata_when_absent(monkeypatch, tmp_path):
    meta_path = tmp_path / "export_meta.json"
    monkeypatch.setenv("EXPORT_META_PATH", str(meta_path))

    client = TestClient(app)
    r = client.get("/api/v2/tickets/export/last")
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("ok") is False
    assert "No export metadata" in payload.get("detail", "")


def test_v2_3_get_last_export_metadata_when_present(monkeypatch, tmp_path):
    meta_path = tmp_path / "export_meta.json"
    monkeypatch.setenv("EXPORT_META_PATH", str(meta_path))
    meta = {
        "timestamp": "2025-10-21T12:00:00Z",
        "filename": "export.xlsx",
        "sharepointUrl": "https://contoso.sharepoint.com/sites/app/export.xlsx",
        "rows": 42,
        "filters": {"group_ids": ["1"], "statuses": ["open"], "ids_csv": None},
    }
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    client = TestClient(app)
    r = client.get("/api/v2/tickets/export/last")
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("ok") is True
    assert payload.get("meta", {}).get("filename") == "export.xlsx"
