from backend.services import zendesk_service as zs


def test_v2_3_build_status_map_coercion():
    # ids as strings and ints should be handled
    tickets = [
        {"id": "1", "status": "open", "updated_at": "t1"},
        {"id": 2, "status": "pending", "updated_at": "t2"},
        {"id": "x", "status": "closed", "updated_at": "t3"},  # ignored
    ]
    m = zs.build_status_map(tickets)
    assert 1 in m and 2 in m
    assert m[1]["status"] == "open"
    assert m[2]["updated_at"] == "t2"


def test_v2_3_enrich_with_resolution_times(monkeypatch):
    # stub both potential upstreams
    def _metrics(_tid: int):
        # return None for first, value for second
        return "2025-01-01T00:00:00Z" if _tid == 2 else None

    def _audits(_tid: int):
        return "2025-02-02T00:00:00Z"

    monkeypatch.setattr(zs, "get_metrics_solved_at", _metrics)
    monkeypatch.setattr(zs, "get_last_resolution_from_audits", _audits)

    m = {1: {"status": "closed"}, 2: {"status": "solved"}, 3: {"status": "open"}}
    zs.enrich_with_resolution_times(m)
    assert m[1]["resolved_at"] == "2025-02-02T00:00:00Z"
    assert m[2]["resolved_at"] == "2025-01-01T00:00:00Z"
    assert "resolved_at" not in m[3]

