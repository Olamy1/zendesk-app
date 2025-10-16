# =================================================================================================
# File: tests/integration/conftest.py
# Purpose:
#   Stable bootstrap for integration tests in the Zendesk App.
#   Provides a real FastAPI TestClient with middleware & routes loaded.
#   Ensures INTEGRATION_MODE and proper environment for end-to-end route tests.
# =================================================================================================

import os
os.environ.update({
    "APP_ENV": "integration",
    "UNIT_MODE": "0",
    "INTEGRATION_MODE": "1",
})

# Guard against downstream overrides
os.environ["PYTEST_INTEGRATION_OVERRIDE"] = "1"
import sys
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import get_settings

# -----------------------------------------------------------------------------------
# 🧭 Ensure Integration Environment
# -----------------------------------------------------------------------------------
def pytest_configure(config):
    """
    Enforce integration mode at pytest startup before any test sessions.
    Ensures this overrides global conftest.py defaults.
    """
    os.environ["APP_ENV"] = "integration"
    os.environ["UNIT_MODE"] = "0"
    os.environ["INTEGRATION_MODE"] = "1"
    os.environ["PYTEST_INTEGRATION_OVERRIDE"] = "1"

    print("🧩 [Integration Override Active] APP_ENV=integration | UNIT_MODE=0 | INTEGRATION_MODE=1")

settings = get_settings()
print("✅ [Integration Bootstrap] MODE=Integration")
print(f"🔗 ZENDESK_API_URL={getattr(settings, 'ZENDESK_API_URL', 'N/A')}")

# -----------------------------------------------------------------------------------
# 🌐 FastAPI Test Client Fixture
# -----------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def integration_client() -> TestClient:
    """
    Provides a real FastAPI TestClient with all routers, middleware, and
    dependency overrides loaded — used for end-to-end API testing.
    """
    with TestClient(app) as client:
        yield client


# -----------------------------------------------------------------------------------
# 🪄 Auth Header Fixture (shared across integration tests)
# -----------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def auth_headers():
    """Generate default auth header for integration tests."""
    token = settings.ZENDESK_API_TOKEN or "valid-token"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    """
    Prevent real Zendesk, SharePoint, or email network calls during integration tests.
    Automatically patches known external dependencies with safe mock implementations.
    """

    # ---------------------------------------------------------------------------------
    # 🎫 Zendesk Ticket Operations
    # ---------------------------------------------------------------------------------
    monkeypatch.setattr(
        "backend.services.zendesk_service.update_ticket",
        lambda tid, **kw: {
            "id": tid,
            "status": kw.get("status", "solved"),
            "updated_at": "2025-10-16T00:00:00Z",
        },
    )

    monkeypatch.setattr(
        "backend.services.zendesk_service.search_by_groups_and_statuses",
        lambda *a, **kw: [
            {"id": 1, "status": "open", "subject": "Mock ticket for integration test"}
        ],
    )

    monkeypatch.setattr(
        "backend.services.zendesk_service.add_comment",
        lambda tid, text, public=False: {
            "id": tid,
            "body": text,
            "public": public,
            "created_at": "2025-10-16T00:00:00Z",
        },
    )

    # ---------------------------------------------------------------------------------
    # 👥 Zendesk User Fetch (Fixes Invalid URL None/users.json errors)
    # ---------------------------------------------------------------------------------
    monkeypatch.setattr(
        "backend.services.zendesk_service.fetch_users",
        lambda role=None: [
            {"id": 1, "name": "Jane Doe", "role": role or "agent"},
            {"id": 2, "name": "John Smith", "role": role or "admin"},
        ],
    )

    # ---------------------------------------------------------------------------------
    # 🗂️ SharePoint Uploads
    # ---------------------------------------------------------------------------------
    monkeypatch.setattr(
        "backend.services.sharepoint_service.upload_bytes",
        lambda name, data: f"https://mocksharepoint.local/{name}",
    )

    # ---------------------------------------------------------------------------------
    # ✉️ Email Notifications
    # ---------------------------------------------------------------------------------
    monkeypatch.setattr(
        "backend.services.email_service.send_directors_export_link",
        lambda url, name: True,
    )

    # ---------------------------------------------------------------------------------
    # ✅ Mock Zendesk Base URL to Avoid Invalid URL Errors
    # ---------------------------------------------------------------------------------
    monkeypatch.setattr(
        "backend.services.zendesk_service.ZENDESK_API_URL",
        "https://mock.zendesk/api/v2",
    )

    yield
