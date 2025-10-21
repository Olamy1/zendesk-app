# =================================================================================================
# File: tests/integration/conftest.py
# Purpose:
#   Stable bootstrap for integration tests in the Zendesk App.
#   Ensures correct environment setup *before* importing backend.main.
#   Provides real FastAPI TestClient with mocks and auth for end-to-end validation.
#
# Version: 2.3.5 | October 2025
# Author: Olivier Lamy
# =================================================================================================

import os
import sys
import pytest
from fastapi.testclient import TestClient

# -------------------------------------------------------------------------------------------------
# 🧭 Early Environment Bootstrap (MUST RUN BEFORE IMPORTS)
# -------------------------------------------------------------------------------------------------
if os.getenv("PYTEST_ENV_LOCKED") == "1" and os.getenv("UNIT_MODE") == "1":
    print("⏭️ [Integration Conftest] Skipped — Root conftest locked UNIT mode.")
else:
    os.environ.update({
        "APP_ENV": "integration",
        "UNIT_MODE": "0",
        "INTEGRATION_MODE": "1",
        "PYTEST_ENV_LOCKED": "1",
        "PYTEST_INTEGRATION_OVERRIDE": "1",
    })
    print(f"🧩 [Integration Bootstrap] APP_ENV={os.getenv('APP_ENV')} | "
          f"UNIT_MODE={os.getenv('UNIT_MODE')} | INTEGRATION_MODE={os.getenv('INTEGRATION_MODE')}")

# -------------------------------------------------------------------------------------------------
# 🌐 Import AFTER environment setup
# -------------------------------------------------------------------------------------------------
from backend.main import app
from backend.config import get_settings

settings = get_settings()
print(f"✅ [Integration Mode Active] ZENDESK_API_URL={getattr(settings, 'ZENDESK_API_URL', 'N/A')}")

# -------------------------------------------------------------------------------------------------
# 🌐 FastAPI Test Client Fixture
# -------------------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def integration_client() -> TestClient:
    """Provides a fully initialized FastAPI TestClient for integration tests."""
    with TestClient(app) as client:
        yield client

# -------------------------------------------------------------------------------------------------
# 🪄 Auth Header Fixture
# -------------------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def auth_headers():
    """Generate default auth header for integration tests."""
    token = settings.ZENDESK_API_TOKEN or "valid-token"
    return {"Authorization": f"Bearer {token}"}

# -------------------------------------------------------------------------------------------------
# 🧩 Mock External Services
# -------------------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    """Prevents real Zendesk, SharePoint, or email network calls during integration tests."""

    # 🎫 Zendesk Ticket Operations
    monkeypatch.setattr(
        "backend.services.zendesk_service.update_ticket",
        lambda tid, **kw: {
            "id": tid,
            "status": kw.get("status", "solved"),
            "updated_at": "2025-10-21T00:00:00Z",
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
            "created_at": "2025-10-21T00:00:00Z",
        },
    )

    # 👥 Zendesk User Fetch
    monkeypatch.setattr(
        "backend.services.zendesk_service.fetch_users",
        lambda role=None: [
            {"id": 1, "name": "Jane Doe", "role": role or "agent"},
            {"id": 2, "name": "John Smith", "role": role or "admin"},
        ],
    )

    # 🗂️ SharePoint Uploads
    monkeypatch.setattr(
        "backend.services.sharepoint_service.upload_bytes",
        lambda name, data: f"https://mocksharepoint.local/{name}",
    )

    # ✉️ Email Notifications
    monkeypatch.setattr(
        "backend.services.email_service.send_directors_export_link",
        lambda url, name: True,
    )

    # ✅ Mock Zendesk Base URL
    monkeypatch.setattr(
        "backend.services.zendesk_service.ZENDESK_API_URL",
        "https://mock.zendesk/api/v2",
    )

    yield

# -------------------------------------------------------------------------------------------------
# 🧩 Optional: Route Sanity Check
# -------------------------------------------------------------------------------------------------
@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Print registered routes for sanity."""
    from fastapi.routing import APIRoute
    routes = [r.path for r in app.routes if isinstance(r, APIRoute)]
    print("🔍 [Integration Route Check] Registered routes:")
    for r in sorted(routes):
        print(f"   • {r}")
    print(f"📦 Total routes: {len(routes)}")
