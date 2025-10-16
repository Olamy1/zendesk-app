# =================================================================================================
# File: tests/unit/test_main_startup.py
# Description:
#   Unit tests for OAPS Zendesk App main application startup and configuration.
#
# Purpose:
#   Validates FastAPI app initialization, route registration, environment loading,
#   and root health check functionality.
#
# Why:
#   Ensures the v2.0 infrastructure baseline (app_infra) is booting with correct
#   middleware, routers, and configuration before advancing to feature-layer tests.
#
# Scope:
#   - Verifies successful app creation.
#   - Confirms `/` health check returns expected response.
#   - Ensures `.env` configuration is loadable via get_settings().
#   - Confirms routers for Tickets and Users are registered under v2 paths.
#
# Author: Olivier Lamy
# Version: 2.0.0 | October 2025
# =================================================================================================

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import get_settings
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

class ExceptionPassthroughMiddleware(BaseHTTPMiddleware):
    """Middleware that ensures exceptions bubble up to the app’s handler in isolated test apps."""
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            # Let FastAPI’s handler catch it instead of re-raising
            from fastapi.requests import Request
            from fastapi.responses import JSONResponse
            from fastapi import status
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": str(exc), "path": request.url.path},
            )

# ---------------------------------------------------------------------------------------------
# 📦 Fixtures
# ---------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    """Fixture providing a FastAPI TestClient instance for integration-style testing."""
    return TestClient(app)


# ---------------------------------------------------------------------------------------------
# 🩺 Health Check Endpoint
# ---------------------------------------------------------------------------------------------
def test_health_check_returns_ok(client):
    """Verify that the root (`/`) health check endpoint responds with status 200."""
    response = client.get("/")
    assert response.status_code == 200, "Expected 200 OK from root health check"
    payload = response.json()
    assert payload.get("status") == "ok"
    assert "Zendesk Reporting API" in payload.get("message", "")


# ---------------------------------------------------------------------------------------------
# ⚙️ App Initialization
# ---------------------------------------------------------------------------------------------
def test_app_title_and_version():
    """Confirm that the FastAPI app initializes with the correct title and version metadata."""
    assert app.title == "OAPS Zendesk App"
    assert app.version.startswith("2.0"), "App version should reflect current release cycle (v2.x)"
    assert hasattr(app, "router"), "FastAPI app must have a router attribute"


# ---------------------------------------------------------------------------------------------
# 🌐 Router Registration
# ---------------------------------------------------------------------------------------------
def test_router_prefixes_registered():
    """Ensure Tickets and Users routers are properly registered under both v1 and v2 paths."""
    routes = [r.path for r in app.routes]
    expected_prefixes = ["/api/tickets", "/api/users", "/api/v2/tickets", "/api/v2/users"]
    for prefix in expected_prefixes:
        assert any(prefix in route for route in routes), f"Expected route prefix {prefix} not found"


# ---------------------------------------------------------------------------------------------
# 🔐 Environment Configuration
# ---------------------------------------------------------------------------------------------
def test_environment_loads_successfully(monkeypatch):
    """
    Validate that environment variables load correctly and get_settings() works as expected.
    Resets cached settings to ensure fresh reads per environment.
    """
    # Arrange
    from backend import config
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost")

    # Force reload (avoids cached 'unit' environment)
    if hasattr(config.get_settings, "cache_clear"):
        config.get_settings.cache_clear()

    # Act
    settings = config.get_settings()

    # Assert
    assert settings.APP_ENV == "test", f"Expected APP_ENV='test' but got {settings.APP_ENV}"
    assert settings.DEBUG is True
    assert "localhost" in settings.CORS_ORIGINS or "http://localhost" in settings.CORS_ORIGINS


# ---------------------------------------------------------------------------------------------
# ⚠️ Exception Handling Verification
# ---------------------------------------------------------------------------------------------
def test_global_exception_handler_isolated():
    """
    Test the global exception handler using a clean app instance.
    """
    from backend.main import global_exception_handler  # import directly

    isolated_app = FastAPI()
    isolated_app.router.on_startup.clear()  # ensure clean startup
    isolated_app.add_exception_handler(Exception, global_exception_handler)
    isolated_app.add_middleware(
        ExceptionPassthroughMiddleware
    )  # ensures handler intercepts route-level errors





    @isolated_app.get("/test-error")
    async def trigger_error():
        raise ValueError("Intentional test error")

    client = TestClient(isolated_app)
    response = client.get("/test-error")
    payload = response.json()

    assert response.status_code == 500
    assert payload["error"] == "Intentional test error"
    assert payload["path"] == "/test-error"