# =====================================================================
# File: tests/unit/test_helpers.py
# Description: Unit tests for utils/helpers.py
# =====================================================================

import pytest
from backend.utils import helpers
import openpyxl



def test_compute_meeting_window(monkeypatch):
    """Check meeting window returns start and end keys"""
    win = helpers.compute_meeting_window()
    assert "start" in win
    assert "end" in win



def test_age_bucket_boundaries():
    assert helpers._age_bucket(0) == "Under 10 Days"
    assert helpers._age_bucket(11) == "Over 10 Days"
    assert helpers._age_bucket(21) == "Over 20 Days"
    assert helpers._age_bucket(31) == "Over 30 Days"


def test_parse_iso_with_and_without_tz():
    naive = "2025-09-30T12:00:00"
    aware = "2025-09-30T12:00:00-04:00"
    dt1 = helpers._parse_iso(naive)
    dt2 = helpers._parse_iso(aware)
    assert dt1.tzinfo is not None
    assert dt2.tzinfo is not None


def test_fill_color_for_age_valid_and_invalid():
    assert helpers._fill_color_for_age("Over 30 Days") is not None
    assert helpers._fill_color_for_age("Invalid Age") is None


def test_make_ticket_workbook_smoke(tmp_path):
    rows = [
        {"id": 1, "subject": "Test", "group": "A", "status": "open",
         "assignee_id": 123, "assignee_name": "Tester",
         "ageBucket": "Over 10 Days", "ageDays": 15, "closedByMeeting": False}
    ]
    data, filename = helpers.make_ticket_workbook(rows)
    out = tmp_path / filename
    out.write_bytes(data)
    wb = openpyxl.load_workbook(out)
    assert "Ticket Breakdown" in "".join(wb.sheetnames)
    assert "Ticket Age (Days)" in [cell.value for cell in wb.active[1]]