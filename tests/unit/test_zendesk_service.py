# =====================================================================
# File: tests/unit/test_zendesk_service.py
# Description: Unit tests for zendesk_service.py
# Author: Olivier Lamy (Refactored)
# =====================================================================

import pytest
import requests # Need to import requests to correctly patch it later
from unittest.mock import MagicMock

# Import the module under test
from backend.services import zendesk_service as zd


# ---------------------------------------------------------------------
# Helper Mock Class
# ---------------------------------------------------------------------

class MockResponse:
    """A standard mock for requests.Response objects."""
    def __init__(self, json_data, status_code=200, headers=None):
        self._json = json_data
        self.status_code = status_code
        self.headers = headers if headers is not None else {}

    def json(self):
        """Returns the JSON payload."""
        return self._json

    def raise_for_status(self):
        """Simulates the requests.raise_for_status behavior."""
        if not (200 <= self.status_code < 300):
            # Use requests.HTTPError for robustness in unit testing
            raise requests.HTTPError(f"HTTP {self.status_code} error")


# ---------------------------------------------------------------------
# Test Helper Functions (_safe_email, _safe_token, build_status_map)
# ---------------------------------------------------------------------

def test_safe_email():
    """Test email masking utility."""
    assert zd._safe_email("user@example.com").startswith("u***@")
    assert zd._safe_email(None) == "hidden"
    assert zd._safe_email("a@b.c") == "a***@b.c"


def test_safe_token():
    """Test token masking utility."""
    assert zd._safe_token("abcdef123456") == "abc...456"
    assert zd._safe_token("123") == "hidden"


def test_build_status_map():
    """Test creation of the status mapping dictionary."""
    tickets = [
        {"id": 1, "status": "open", "updated_at": "2025-09-29"},
        {"id": "2", "status": "solved", "updated_at": "2025-09-28"},
        {"id": "abc", "status": "ignored", "updated_at": "2025-09-27"},
    ]
    result = zd.build_status_map(tickets)
    assert isinstance(result, dict)
    assert 1 in result and 2 in result
    assert "abc" not in result # Non-digit IDs should be ignored
    assert result[1]["status"] == "open"


# ---------------------------------------------------------------------
# Test Service Functions (update_ticket, add_comment)
# ---------------------------------------------------------------------

# Note: The easiest way to mock Zendesk calls when _retry is used is to mock _retry itself.

def test_update_ticket_success(mocker):
    """Test successful ticket update."""
    
    # Mock the _retry helper function to return a successful response
    mock_response = MockResponse({"ticket": {"id": 123, "status": "open", "assignee_id": 456}})
    mock_retry = mocker.patch("backend.services.zendesk_service._retry", return_value=mock_response)
    
    # Mock _get_config, as it is called by _retry's call to _auth (via _auth)
    mocker.patch("backend.services.zendesk_service._get_config", return_value={
        'base_url': 'https://mock.zendesk.com/api/v2',
        'email': 'u@e.com',
        'token': 't'
    })

    result = zd.update_ticket(123, status="open", assignee_id=456)
    
    # Assertions on the result
    assert result["id"] == 123
    assert result["status"] == "open"
    assert result["assignee_id"] == 456
    
    # Assertions on the mock call (ensure it was called with PUT)
    # The actual call signature is inside zd._retry, so we only check _retry was called
    mock_retry.assert_called_once()


def test_update_ticket_failure_raises(mocker):
    """Test that failed API call raises an exception."""

    # Mock _retry to return a 500 error
    mock_response = MockResponse({"error": "failed"}, status_code=500)
    # This time, we mock the function being passed to _retry: requests.put
    mocker.patch("requests.put", return_value=mock_response)
    
    # We must patch _retry itself, as it calls raise_for_status
    # We mock _retry to execute the real requests.put call (which we just patched)
    # OR, we mock _retry to return the failing response and let it handle the error.
    
    # Cleanest way: Mock _retry to return the failing response
    failing_response = MockResponse({"error": "failed"}, status_code=500)
    mocker.patch("backend.services.zendesk_service._retry", side_effect=requests.HTTPError("HTTP 500"))

    with pytest.raises(requests.HTTPError):
        # zd.update_ticket will call _retry, which will raise HTTPError immediately
        zd.update_ticket(1, status="open")


def test_add_comment_success(mocker):
    """Test successful addition of a comment."""
    
    # Mock _retry to return a successful response containing the ticket/comment data
    mock_data = {"ticket": {"id": 1, "comment": {"body": "hi", "public": True}}}
    mock_response = MockResponse(mock_data, 200)
    mocker.patch("backend.services.zendesk_service._retry", return_value=mock_response)
    
    # Mock config helper as it's needed by the service function's internal calls
    mocker.patch("backend.services.zendesk_service._get_config", return_value={
        'base_url': 'https://mock.zendesk.com/api/v2',
        'email': 'u@e.com',
        'token': 't'
    })

    result = zd.add_comment(1, "hi", public=True)
    
    assert result["id"] == 1
    # Note: Zendesk PUT response usually contains the full ticket, not just the comment block, 
    # but the test asserts on the fields it cares about.
    # The assertion below is based on the logic in your original test.
    assert result["comment"]["body"] == "hi"
    assert result["comment"]["public"] is True


# ---------------------------------------------------------------------
# Test Metrics and Audits (enrich_with_resolution_times)
# ---------------------------------------------------------------------

def test_enrich_with_resolution_times_modifies_map(mocker):
    """Test that a solved ticket is enriched with a resolved_at timestamp."""
    
    # Mock the two internal functions used for resolution time
    mock_metrics = mocker.patch("backend.services.zendesk_service.get_metrics_solved_at", 
                                return_value="2025-09-01T10:00:00Z")
    mock_audits = mocker.patch("backend.services.zendesk_service.get_last_resolution_from_audits", 
                               return_value=None) # Should not be called
    
    smap = {
        1: {"status": "solved", "updated_at": "2025-09-01T11:00:00Z"},
        2: {"status": "open", "updated_at": "2025-09-01T11:00:00Z"}
    }
    
    zd.enrich_with_resolution_times(smap)
    
    assert smap[1].get("resolved_at") == "2025-09-01T10:00:00Z"
    assert "resolved_at" not in smap[2]
    mock_metrics.assert_called_once_with(1)
    mock_audits.assert_not_called()


def test_enrich_audits_fallback(mocker):
    """Test that audit fallback is used if metrics fail."""
    
    # Metrics fails (raises exception) or returns None
    mocker.patch("backend.services.zendesk_service.get_metrics_solved_at", 
                 side_effect=Exception("Metrics API Down"))
    
    # Audits succeeds
    mock_audits = mocker.patch("backend.services.zendesk_service.get_last_resolution_from_audits", 
                               return_value="2025-09-02T12:00:00Z") 
    
    smap = {
        1: {"status": "closed", "updated_at": "2025-09-03T00:00:00Z"},
    }
    
    zd.enrich_with_resolution_times(smap)
    
    assert smap[1].get("resolved_at") == "2025-09-02T12:00:00Z"
    mock_audits.assert_called_once_with(1)


def test_enrich_with_resolution_times_handles_empty():
    """Test that the function handles an empty map without error."""
    smap = {}
    zd.enrich_with_resolution_times(smap)
    assert smap == {}


# ---------------------------------------------------------------------
# Test API wrappers (show_many, search_by_groups_and_statuses)
# ---------------------------------------------------------------------

def test_show_many_fetches_batches(mocker):
    """Test that show_many handles batches and returns a combined list."""
    
    # Mock _retry to return two pages of tickets
    mock_page1 = MockResponse({"tickets": [{"id": i} for i in range(1, 101)]})
    mock_page2 = MockResponse({"tickets": [{"id": 101}]})
    
    # Use side_effect to provide responses sequentially
    mock_retry = mocker.patch("backend.services.zendesk_service._retry", 
                              side_effect=[mock_page1, mock_page2])
    
    # Mock config helper
    mocker.patch("backend.services.zendesk_service._get_config", return_value={
        'base_url': 'https://mock.zendesk.com/api/v2',
        'email': 'u@e.com',
        'token': 't'
    })

    ticket_ids = [str(i) for i in range(1, 102)]
    result = zd.show_many(ticket_ids)
    
    assert len(result) == 101
    assert mock_retry.call_count == 2
    
    # Check that URLs were formatted correctly (e.g., batching 1-100 and 101)
    args1, _ = mock_retry.call_args_list[0]
    args2, _ = mock_retry.call_args_list[1]
    assert "ids=1,2,3" in args1[1] # Check part of first batch
    assert "ids=101" in args2[1] # Check second batch

    
def test_search_by_groups_and_statuses(mocker):
    """Test the pagination and query construction of the search API."""
    
    # Mock responses for two pages of search results
    search_page1 = MockResponse({
        "results": [{"id": 10, "result_type": "ticket", "status": "open"}],
        "next_page": "https://mock.zendesk.com/api/v2/search.json?page=2",
    })
    search_page2 = MockResponse({
        "results": [{"id": 20, "result_type": "ticket", "status": "pending"}],
        "next_page": None,
    })
    
    mocker.patch("backend.services.zendesk_service._retry", 
                 side_effect=[search_page1, search_page2])
    
    # Mock config helper
    mocker.patch("backend.services.zendesk_service._get_config", return_value={
        'base_url': 'https://mock.zendesk.com/api/v2',
        'email': 'u@e.com',
        'token': 't'
    })

    group_ids = ["1", "2"]
    statuses = ["open", "pending"]
    result = zd.search_by_groups_and_statuses(group_ids, statuses)
    
    assert len(result) == 2
    assert result[0]['id'] == 10
    
    # Check that pagination occurred
    mock_retry = zd._retry
    assert mock_retry.call_count == 2
    
    # Check that the query was constructed correctly
    args1, _ = mock_retry.call_args_list[0]
    search_url = args1[1] # The URL passed to the GET request
    assert "query=type%3Aticket%20%28group_id%3A1%20OR%20group_id%3A2%29%20%28status%3Aopen%20OR%20status%3Apending%29" in search_url