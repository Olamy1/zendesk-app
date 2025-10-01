# =====================================================================
# File: tests/unit/test_main.py
# Description: Unit tests for backend/main.py
# Framework: pytest + httpx (TestClient)
# =====================================================================

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check_root():
    """Root endpoint should return API status ok"""
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "Zendesk Reporting API is running" in body["message"]
