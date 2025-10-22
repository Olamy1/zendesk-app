from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.utils.error_handler import generic_exception_handler


def test_v2_3_error_handler_returns_json():
    app = FastAPI()
    app.add_exception_handler(Exception, generic_exception_handler)

    @app.get("/boom")
    def boom():
        raise RuntimeError("explode")

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.status_code == 500
    j = r.json()
    assert j["error"] == "explode"
    assert j["path"] == "/boom"
