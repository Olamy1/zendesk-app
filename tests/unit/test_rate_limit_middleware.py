# =================================================================================================
# File: tests/unit/test_rate_limit_middleware.py
# Description: Unit tests for RateLimitMiddleware.
# Author: Olivier Lamy | Version: 1.0.0 | October 2025
# =================================================================================================

import time
import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from backend.middleware.rate_limit import RateLimitMiddleware, _request_cache, MAX_REQUESTS_PER_IP

# -------------------------------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------------------------------
# Force middleware activation for this test file
@pytest.fixture(autouse=True)
def _activate_rate_limit(monkeypatch):
    """
    Overrides environment to enable rate limiting during these tests.
    """
    monkeypatch.setenv("UNIT_MODE", "0")
    monkeypatch.setenv("APP_ENV", "dev")  # any non-test value
    _request_cache.clear()
    yield
    _request_cache.clear()

@pytest.fixture
def app():
    """Creates a simple FastAPI app with rate limiting applied."""
    app = FastAPI()

    @app.get("/api/test")
    async def api_test():
        return JSONResponse({"ok": True})

    @app.get("/")
    async def root():
        return JSONResponse({"ok": True})

    app.add_middleware(RateLimitMiddleware)
    return app


@pytest.fixture
def client(app):
    """Provides a TestClient for the app."""
    return TestClient(app)


# -------------------------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------------------------
def test_rate_limit_allows_within_limit(client):
    """Should allow requests within the MAX_REQUESTS_PER_IP limit."""
    _request_cache.clear()
    for _ in range(MAX_REQUESTS_PER_IP):
        resp = client.get("/api/test")
        assert resp.status_code == 200
    assert len(_request_cache) == 1


def test_rate_limit_exceeds_limit_returns_429(client):
    """Should return 429 when client exceeds MAX_REQUESTS_PER_IP."""
    _request_cache.clear()
    for _ in range(MAX_REQUESTS_PER_IP + 1):
        resp = client.get("/api/test")
    assert resp.status_code == 429
    assert "Rate limit exceeded" in resp.json()["detail"]


def test_rate_limit_bypasses_docs_and_root(client):
    """Should skip enforcement for root/docs paths."""
    _request_cache.clear()
    resp = client.get("/")
    assert resp.status_code == 200
    resp_docs = client.get("/docs")
    assert resp_docs.status_code == 200
    assert len(_request_cache) == 0


def test_rate_limit_resets_after_window(monkeypatch, client):
    """Should clear old entries after RATE_LIMIT_WINDOW expires."""
    _request_cache.clear()
    now = time.time()
    client_ip = "127.0.0.1"
    _request_cache[client_ip] = [now - 120]  # older than 60s window

    # monkeypatch time to simulate now
    monkeypatch.setattr("backend.middleware.rate_limit.time.time", lambda: now)
    resp = client.get("/api/test")
    assert resp.status_code == 200
    # Old timestamps should be pruned, leaving one
    assert len(_request_cache[client_ip]) == 1


def test_rate_limit_skips_unit_mode(monkeypatch):
    """Should bypass rate limiting entirely in UNIT_MODE=1."""
    monkeypatch.setenv("UNIT_MODE", "1")
    app = FastAPI()

    @app.get("/api/test")
    async def api_test():
        return JSONResponse({"ok": True})

    app.add_middleware(RateLimitMiddleware)
    client = TestClient(app)
    resp = client.get("/api/test")
    assert resp.status_code == 200
    monkeypatch.delenv("UNIT_MODE", raising=False)
