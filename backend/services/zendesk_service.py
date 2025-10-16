# =====================================================================
# File: backend/services/zendesk_service.py
# Description: Zendesk API wrapper functions, handling authentication,
#              retries, and core ticket/user/metrics operations.
# Author: OAPS QA Analytics Team
# =====================================================================

import os, time, requests
from typing import Iterable, List, Dict, Any, Optional
from backend.utils.logger import get_logger


logger = get_logger("zendesk_service")

# 🚨 PATCH 1: REMOVE top-level environment variable access 🚨
# ZD_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")
# ZD_EMAIL     = os.getenv("ZENDESK_EMAIL")
# ZD_API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
# BASE = f"https://{ZD_SUBDOMAIN}.zendesk.com/api/v2"
# OAPS_GROUP_IDS = [gid.strip() for gid in os.getenv("OAPS_GROUP_IDS", "").split(",") if gid.strip()]


# 🚨 PATCH 2: ADD helper to safely retrieve config at runtime 🚨
def _get_config() -> Dict[str, Any]:
    """Retrieves all necessary Zendesk config from environment variables."""
    subdomain = os.getenv("ZENDESK_SUBDOMAIN")
    email = os.getenv("ZENDESK_EMAIL")
    token = os.getenv("ZENDESK_API_TOKEN")

    config = {
        "subdomain": subdomain,
        "email": email,
        "token": token,
        "base_url": f"https://{subdomain}.zendesk.com/api/v2" if subdomain else None,
        "oaps_group_ids": [
            gid.strip() for gid in os.getenv("OAPS_GROUP_IDS", "").split(",") if gid.strip()
        ],
    }
    
    # Safe startup log (moved inside this function, which runs first)
    logger.info(
        f"Zendesk service config loaded (subdomain={_safe_token(config['subdomain'])}, email={_safe_email(config['email'])}, token={_safe_token(config['token'])})"
    )
    
    return config

# -------------------
# Helper Functions
# -------------------

def _safe_email(email: Optional[str]) -> str:
    """Mask email for logs: j***@domain.com"""
    if not email or "@" not in email:
        return "hidden"
    local, _, domain = email.partition("@")
    return f"{local[0]}***@{domain}"


def _safe_token(token: Optional[str]) -> str:
    """Mask token for logs: abc...xyz (first 3 + last 3 chars)"""
    if not token or len(token) < 6:
        return "hidden"
    return f"{token[:3]}...{token[-3:]}"


# 🚨 PATCH 3: Update _auth to use _get_config 🚨
def _auth():
    config = _get_config()
    return (f"{config['email']}/token", config['token'])


# 🚨 PATCH 4: REMOVE the old top-level logger.info() call 🚨
# logger.info(
#    f"Zendesk service initialized (subdomain={ZD_SUBDOMAIN}, email={_safe_email(ZD_EMAIL)}, token={_safe_token(ZD_API_TOKEN)})"
# )


def _retry(req_callable, *args, **kwargs):
    """Handles Zendesk rate limiting and retries once on 429."""
    r = req_callable(*args, **kwargs)
    if r.status_code == 429:
        wait = int(r.headers.get("Retry-After", "3")) + 1
        logger.warning(f"429 rate limit hit. Retrying after {wait}s...")
        time.sleep(wait)
        r = req_callable(*args, **kwargs)
    r.raise_for_status()
    return r


# -------------------
# Tickets
# -------------------

# 🚨 PATCH 5: Update all service functions to use BASE/OAPS_GROUP_IDS from _get_config 🚨

def show_many(ticket_ids: Iterable[str]) -> List[Dict[str, Any]]:
    config = _get_config() # <-- Get config at runtime
    BASE = config['base_url']

    ids = [s for s in ticket_ids if s.isdigit()]
    if not ids:
        return []
    out: List[Dict[str, Any]] = []
    logger.info(f"Fetching {len(ids)} tickets via show_many")
    for i in range(0, len(ids), 100):
        q = ",".join(ids[i:i+100])
        url = f"{BASE}/tickets/show_many.json?ids={q}"
        logger.debug(f"GET {url}")
        r = _retry(requests.get, url, auth=_auth(), timeout=30)
        tickets = r.json().get("tickets", [])
        logger.debug(f"Fetched {len(tickets)} tickets in batch {i//100+1}")
        out.extend(tickets)
    return out


def search_by_groups_and_statuses(group_ids: Optional[List[str]], statuses: Optional[List[str]]) -> List[Dict[str, Any]]:
    config = _get_config() # <-- Get config at runtime
    BASE = config['base_url']
    
    """Uses Zendesk search API. Adjust query per your dataset (e.g., brand:, type:ticket)."""
    q = ["type:ticket"]
    if group_ids:
        q.append("(" + " OR ".join([f"group_id:{gid}" for gid in group_ids if gid]) + ")")
    if statuses:
        q.append("(" + " OR ".join([f"status:{s}" for s in statuses if s]) + ")")
    query = " ".join(q) if q else "type:ticket"

    url = f"{BASE}/search.json?query={requests.utils.quote(query)}&per_page=100"
    logger.info(f"Searching tickets: {query}")
    out: List[Dict[str, Any]] = []
    while url:
        logger.debug(f"GET {url}")
        r = _retry(requests.get, url, auth=_auth(), timeout=30)
        data = r.json()
        results = data.get("results", [])
        logger.debug(f"Fetched {len(results)} results in search page")
        out.extend(results)
        url = data.get("next_page")
        time.sleep(0.1)
    # Normalize result shape to 'ticket-like'
    norm = []
    for t in out:
        if t.get("result_type") != "ticket":
            continue
        norm.append({
            "id": t["id"],
            "subject": t.get("subject"),
            "status": t.get("status"),
            "created_at": t.get("created_at"),
            "updated_at": t.get("updated_at"),
            "assignee_id": t.get("assignee_id"),
            "group_id": t.get("group_id"),
        })
    logger.info(f"Search returned {len(norm)} tickets after normalization")
    return norm


def update_ticket(ticket_id: int, **fields) -> Dict[str, Any]:
    config = _get_config() # <-- Get config at runtime
    BASE = config['base_url']
    
    url = f"{BASE}/tickets/{ticket_id}.json"
    logger.info(f"Updating ticket {ticket_id} with {fields}")
    r = _retry(requests.put, url, auth=_auth(), json={"ticket": fields}, timeout=30)
    ticket = r.json()["ticket"]
    logger.debug(f"Ticket {ticket_id} updated → status={ticket.get('status')}, assignee_id={ticket.get('assignee_id')}, group_id={ticket.get('group_id')}")
    return ticket


def add_comment(ticket_id: int, body: str, public: bool = False) -> Dict[str, Any]:
    config = _get_config() # <-- Get config at runtime
    BASE = config['base_url']
    
    url = f"{BASE}/tickets/{ticket_id}.json"
    payload = {"ticket": {"comment": {"body": body, "public": public}}}
    logger.info(f"Adding {'public' if public else 'internal'} comment to ticket {ticket_id}")
    r = _retry(requests.put, url, auth=_auth(), json=payload, timeout=30)
    ticket = r.json()["ticket"]
    logger.debug(f"Comment added to ticket {ticket_id}")
    return ticket


# -------------------
# Metrics
# -------------------

def get_metrics_solved_at(ticket_id: int) -> Optional[str]:
    config = _get_config() # <-- Get config at runtime
    BASE = config['base_url']
    
    url = f"{BASE}/tickets/{ticket_id}/metrics.json"
    logger.debug(f"Fetching metrics for ticket {ticket_id}")
    r = _retry(requests.get, url, auth=_auth(), timeout=30)
    m = r.json().get("ticket_metric") or {}
    return m.get("solved_at")


def get_last_resolution_from_audits(ticket_id: int) -> Optional[str]:
    config = _get_config() # <-- Get config at runtime
    BASE = config['base_url']

    url = f"{BASE}/tickets/{ticket_id}/audits.json"
    last = None
    logger.debug(f"Scanning audits for ticket {ticket_id}")
    while url:
        r = _retry(requests.get, url, auth=_auth(), timeout=30)
        data = r.json() or {}
        for audit in data.get("audits", []):
            when = audit.get("created_at")
            for ev in audit.get("events", []):
                if isinstance(ev, dict) and ev.get("type") == "Change" and ev.get("field") == "status":
                    val = (ev.get("value") or "").lower()
                    if val in {"solved", "closed"}:
                        last = when
            url = data.get("next_page")
            time.sleep(0.1)
    if last:
        logger.debug(f"Ticket {ticket_id} last resolution from audits: {last}")
    return last


def build_status_map(tickets: List[Dict[str, Any]]) -> Dict[int, Dict[str, str]]:
    m: Dict[int, Dict[str, str]] = {}
    logger.debug(f"Building status map for {len(tickets)} tickets")
    for t in tickets:
        tid = t.get("id")
        if not isinstance(tid, int) and isinstance(tid, str) and tid.isdigit():
            tid = int(tid)
        if not isinstance(tid, int):
            continue
        m[tid] = {"status": t.get("status", ""), "updated_at": t.get("updated_at", "")}
    return m


def enrich_with_resolution_times(status_map: Dict[int, Dict[str, str]]) -> None:
    logger.debug(f"Enriching {len(status_map)} tickets with resolution times")
    for tid, info in list(status_map.items()):
        st = (info.get("status") or "").lower()
        if st not in {"solved", "closed"}:
            continue
        solved = None
        try:
            solved = get_metrics_solved_at(tid)
        except Exception as e:
            logger.warning(f"Metrics fetch failed for {tid}: {e}")
            solved = None
        if not solved:
            try:
                solved = get_last_resolution_from_audits(tid)
            except Exception as e:
                logger.warning(f"Audit fetch failed for {tid}: {e}")
                solved = None
        if solved:
            info["resolved_at"] = solved
            logger.debug(f"Ticket {tid} resolved_at={solved}")


# -------------------
# Users
# -------------------

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    config = _get_config() # <-- Get config at runtime
    BASE = config['base_url']
    
    """Fetch one user by ID (for reassignment enrichment)."""
    url = f"{BASE}/users/{user_id}.json"
    logger.debug(f"Fetching user {user_id}")
    r = _retry(requests.get, url, auth=_auth(), timeout=30)
    u = r.json().get("user")
    if not u:
        return None
    return {"id": u["id"], "name": u.get("name"), "group_id": u.get("group_id")}


def list_oaps_users() -> List[Dict[str, Any]]:
    config = _get_config() # <-- Get config at runtime
    BASE = config['base_url']
    OAPS_GROUP_IDS = config['oaps_group_ids']
    
    """Fetch all Zendesk agents in OAPS groups only."""
    url = f"{BASE}/users.json?role=agent&per_page=100"
    out: List[Dict[str, Any]] = []
    while url:
        logger.debug(f"GET {url}")
        r = _retry(requests.get, url, auth=_auth(), timeout=30)
        data = r.json()
        for u in data.get("users", []):
            if not OAPS_GROUP_IDS or str(u.get("group_id")) in OAPS_GROUP_IDS:
                out.append({
                    "id": u["id"],
                    "name": u.get("name"),
                    "group_id": u.get("group_id")
                })
        url = data.get("next_page")
        time.sleep(0.1)
    logger.info(f"Fetched {len(out)} OAPS users")
    return out