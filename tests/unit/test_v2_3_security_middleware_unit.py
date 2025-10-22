from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
import os

from backend.middleware.security import TokenAuthMiddleware


def make_app():
    app = FastAPI()
    app.add_middleware(TokenAuthMiddleware)

    @app.get("/")
    def root():
        return {"ok": True}

    @app.get("/api/protected")
    def protected():
        return {"ok": True}

    return app


def test_v2_3_sec_missing_header(monkeypatch):
    monkeypatch.setenv("APP_ENV", "integration")
    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)
    client = TestClient(make_app())
    r = client.get("/api/protected")
    assert r.status_code == 401


def test_v2_3_sec_invalid_format(monkeypatch):
    monkeypatch.setenv("APP_ENV", "integration")
    monkeypatch.setenv("API_AUTH_TOKEN", "abc")
    client = TestClient(make_app())
    r = client.get("/api/protected", headers={"Authorization": "Token abc"})
    assert r.status_code == 401


def test_v2_3_sec_invalid_token(monkeypatch):
    monkeypatch.setenv("APP_ENV", "integration")
    monkeypatch.setenv("API_AUTH_TOKEN", "expected")
    client = TestClient(make_app())
    r = client.get("/api/protected", headers={"Authorization": "Bearer wrong"})
    assert r.status_code == 403


def test_v2_3_sec_valid_token(monkeypatch):
    monkeypatch.setenv("APP_ENV", "integration")
    monkeypatch.setenv("API_AUTH_TOKEN", "expected")
    client = TestClient(make_app())
    r = client.get("/api/protected", headers={"Authorization": "Bearer expected"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_v2_3_sec_bypass_root(monkeypatch):
    monkeypatch.setenv("APP_ENV", "integration")
    client = TestClient(make_app())
    r = client.get("/")
    assert r.status_code == 200


def test_v2_3_sec_safe_env_bypass(monkeypatch):
    monkeypatch.setenv("APP_ENV", "local")
    client = TestClient(make_app())
    # No Authorization header required in SAFE_ENVS
    r = client.get("/api/protected")
    assert r.status_code == 200
