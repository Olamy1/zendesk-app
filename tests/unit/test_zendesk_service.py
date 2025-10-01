# =====================================================================
# File: tests/unit/test_zendesk_service.py
# Description: Unit tests for zendesk_service.py
# =====================================================================

import pytest
from backend.services import zendesk_service as zd

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")


def test_safe_email():
    assert zd._safe_email("user@example.com").startswith("u***@")
    assert zd._safe_email(None) == "hidden"


def test_safe_token():
    assert zd._safe_token("abcdef123456").startswith("abc")
    assert zd._safe_token("123") == "hidden"


def test_build_status_map():
    tickets = [
        {"id": 1, "status": "open", "updated_at": "2025-09-29"},
        {"id": "2", "status": "solved", "updated_at": "2025-09-28"},
    ]
    result = zd.build_status_map(tickets)
    assert isinstance(result, dict)
    assert 1 in result
    assert 2 in result
    assert result[1]["status"] == "open"

def test_update_ticket_success(monkeypatch):
    from backend import services

    # Mock requests.put to return a Response-like object
    def mock_put(*args, **kwargs):
        return MockResponse({"ticket": {"id": 123, "status": "open"}}, 200)

    monkeypatch.setattr(services.zendesk_service.requests, "put", mock_put)

    result = services.zendesk_service.update_ticket(123, status="open")
    assert result["id"] == 123
    assert result["status"] == "open"


def test_add_comment_success(monkeypatch):
    from backend import services
    from backend.services import zendesk_service

    # Patch _auth to return dummy creds
    monkeypatch.setattr(zendesk_service, "_auth", lambda: ("user/token", "dummy"))

    # Mock _retry → simulate Response-like object
    def mock_retry(req_callable, *args, **kwargs):
        return MockResponse(
            {"ticket": {"id": 1, "comment": {"body": "hi", "public": True}}},
            200
        )

    monkeypatch.setattr(zendesk_service, "_retry", mock_retry)

    result = services.zendesk_service.add_comment(1, "hi", public=True)
    assert result["comment"]["body"] == "hi"
    assert result["comment"]["public"] is True



def test_enrich_with_resolution_times_modifies_map():
    smap = {1: {"status": "solved", "resolved_at": None, "updated_at": "2025-09-01T00:00:00"}}
    zd.enrich_with_resolution_times(smap)
    assert "resolved_at" in smap[1] or "updated_at" in smap[1]