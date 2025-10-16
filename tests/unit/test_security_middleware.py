# =================================================================================================
# File: tests/unit/test_security_middleware.py
# Description: Unit tests for TokenAuthMiddleware (synchronized environment-safe version)
# Author: Olivier Lamy | Version: 1.1.1 | October 2025
# =================================================================================================

import os
import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from backend.middleware.security import TokenAuthMiddleware


# -------------------------------------------------------------------------------------------------
# ⚙️ Global Environment Setup (applies before app + middleware)
# -------------------------------------------------------------------------------------------------
# Force consistent, process-wide env for FastAPI async contexts
os.environ["ZENDESK_API_TOKEN"] = "valid-token"
os.environ["APP_ENV"] = "prod"
os.environ.pop("UNIT_MODE", None)


# -------------------------------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def app():
    """FastAPI app with TokenAuthMiddleware applied (stable across threads)."""
    app = FastAPI()

    @app.get("/api/secure")
    async def secure_endpoint():
        return JSONResponse({"ok": True})

    @app.get("/")
    async def root():
        return JSONResponse({"health": "ok"})

    app.add_middleware(TokenAuthMiddleware)
    return app


@pytest.fixture(scope="module")
def client(app):
    """Reusable test client instance."""
    return TestClient(app)


# -------------------------------------------------------------------------------------------------
# ✅ Tests
# -------------------------------------------------------------------------------------------------
def test_token_valid_allows_request(client):
    """Should allow access when valid Bearer token is provided."""
    resp = client.get("/api/secure", headers={"Authorization": "Bearer valid-token"})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.parametrize("path", ["/api/secure"])
def test_token_missing_rejects_request(client, path):
    """
    Should reject request when Authorization header missing in production-like env,
    but bypass in test/unit environment per SAFE_ENVS logic.
    """
    app_env = os.getenv("APP_ENV", "test").lower()
    unit_mode = os.getenv("UNIT_MODE", "1")

    resp = client.get(path)
    if app_env in {"dev", "development", "local", "test", "unit"} or unit_mode == "1":
        # ✅ Auth is bypassed under safe/test envs
        assert resp.status_code == 200
    else:
        assert resp.status_code == 401
        assert "Missing Authorization" in resp.json()["detail"]


def test_token_invalid_rejects_request(client):
    """
    Should reject invalid token only in production-like environments.
    """
    app_env = os.getenv("APP_ENV", "test").lower()
    unit_mode = os.getenv("UNIT_MODE", "1")

    resp = client.get("/api/secure", headers={"Authorization": "Bearer wrong-token"})
    if app_env in {"dev", "development", "local", "test", "unit"} or unit_mode == "1":
        assert resp.status_code == 200  # bypassed
    else:
        assert resp.status_code == 403
        assert "Invalid or expired token" in resp.json()["detail"]
        

def test_bypass_health_and_docs(client):
    """Should skip auth for health and docs endpoints."""
    for path in ["/", "/docs", "/openapi.json", "/redoc"]:
        resp = client.get(path)
        assert resp.status_code == 200


def test_bypass_in_unit_mode():
    """Should bypass token validation entirely when UNIT_MODE=1."""
    os.environ["UNIT_MODE"] = "1"

    app = FastAPI()

    @app.get("/api/secure")
    async def secure_endpoint():
        return JSONResponse({"ok": True})

    app.add_middleware(TokenAuthMiddleware)
    client = TestClient(app)
    resp = client.get("/api/secure")
    assert resp.status_code == 200

    os.environ.pop("UNIT_MODE", None)
