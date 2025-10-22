# =================================================================================================
# File: backend/routers/tickets.py
# Purpose:
#   FastAPI router providing endpoints for ticket operations, including:
#       • Retrieving ticket data from Zendesk
#       • Computing meeting windows
#       • Updating ticket statuses and assignees
#       • Adding comments
#       • Exporting datasets to SharePoint and emailing reports
#       • Listing OAPS users
#
# Behavior:
#   • Reads global app state through environment variables and shared settings.
#   • Automatically bypasses external calls in UNIT_MODE or local/test environments.
#   • Logs each action for traceability.
#   • Wraps all service calls (Zendesk, SharePoint, Email) in robust try/except handlers.
#   • Returns consistent JSON responses with `ok`, `detail`, and relevant data.
#
# Dependencies:
#   - backend.services.zendesk_service (zd)
#   - backend.services.sharepoint_service (sp)
#   - backend.services.email_service (mail)
#   - backend.utils.helpers (compute_meeting_window, build_ticket_rows, make_ticket_workbook)
#   - backend.utils.logger (get_logger)
#
# Version: 2.2.0 | October 2025
# Author: Olivier Lamy
# ============================================================================================

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Body, Query, Depends, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List

# ✅ Correct service imports (single consistent pattern)
from backend.services import zendesk_service as zd
from backend.services.zendesk_service import update_ticket
from backend.services import sharepoint_service
from backend.services import email_service

# ✅ Schemas
from backend.schemas.comment_schema import Comment
from backend.schemas.ticket_schema import Ticket
from backend.schemas.user_schema import User

# ✅ Utilities
from backend.utils import helpers
compute_meeting_window = helpers.compute_meeting_window  # backward-compat for tests
build_ticket_rows = helpers.build_ticket_rows            # backward-compat for tests
make_ticket_workbook = helpers.make_ticket_workbook      # backward-compat for tests
from backend.utils.logger import get_logger

# 🧩 Local logger
logger = get_logger("tickets_router")

# ⚙️ Router
router = APIRouter()

def is_unit_mode() -> bool:
    """Dynamic check for UNIT_MODE to support pytest overrides."""
    return os.getenv("UNIT_MODE", "0") == "1"

def require_auth(request: Request):
    """Enforce auth for v1 endpoints unless explicitly in UNIT_MODE."""
    if os.getenv("UNIT_MODE", "0") == "1":
        return
    hdr = request.headers.get("Authorization")
    if not hdr or not hdr.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = hdr.split("Bearer ", 1)[-1].strip()
    valid = (
        os.getenv("API_AUTH_TOKEN")
        or os.getenv("ZENDESK_API_TOKEN")
        or os.getenv("ZENDESK_TOKEN")
    )
    if not valid or token != valid:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

# Paths (resolve dynamically to respect runtime env changes/monkeypatches)
def _get_export_meta_path() -> Path:
    return Path(os.getenv("EXPORT_META_PATH", "backend/data/export_meta.json"))

def _ensure_parent_dir(p: Path) -> None:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

def _write_export_meta(meta: dict) -> None:
    path = _get_export_meta_path()
    _ensure_parent_dir(path)
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception:
        # Do not fail the main request on metadata write issues
        logger.warning("Failed to write export metadata", exc_info=True)

def _read_export_meta() -> dict:
    try:
        path = _get_export_meta_path()
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        logger.warning("Failed to read export metadata", exc_info=True)
    return {}


# New endpoint: GET /api/tickets/meeting-window
@router.get("/meeting-window")
def get_meeting_window():
    logger.info("Fetching meeting window")
    # Call through the alias so unit tests that monkeypatch
    # backend.routers.tickets.compute_meeting_window take effect
    return compute_meeting_window()


@router.get("/tickets", response_model=Dict[str, Any], dependencies=[Depends(require_auth)])
def get_tickets(
    request: Request,
    group_ids: Optional[str] = Query(default=None, description="CSV of Zendesk group IDs"),
    statuses: Optional[str] = Query(default=None, description="CSV of statuses (open,pending,on-hold,solved,closed)"),
    ids_csv: Optional[str] = Query(default=None, description="CSV of explicit ticket IDs"),
    bucketed: bool = True
) -> Dict[str, Any]:
    """
    Returns enriched ticket rows for the frontend.
    """
    # Extra safeguard in integration/prod: enforce auth inside handler
    try:
        require_auth(request)
    except HTTPException:
        raise
    logger.info(f"Fetching tickets (group_ids={group_ids}, statuses={statuses}, ids_csv={ids_csv}, bucketed={bucketed})")

    # Normalize parameters
    group_ids_list = [g.strip() for g in group_ids.split(",")] if group_ids and group_ids.strip() else None
    statuses_list = [s.strip() for s in statuses.split(",")] if statuses and statuses.strip() else None

    # Get tickets
    if ids_csv:
        ticket_ids = [s.strip() for s in ids_csv.split(",") if s.strip().isdigit()]
        tickets = zd.show_many(ticket_ids)
        logger.info(f"Fetched {len(tickets)} tickets via show_many")
    else:
        tickets = zd.search_by_groups_and_statuses(
            group_ids=group_ids_list,
            statuses=statuses_list
        )
        logger.info(f"Fetched {len(tickets)} tickets via search")

    # Enrich with resolved_at via metrics or audits (only for solved/closed)
    status_map = zd.build_status_map(tickets)
    zd.enrich_with_resolution_times(status_map)

    win = compute_meeting_window()
    rows = build_ticket_rows(tickets, status_map, win, bucketed=bucketed)
    logger.info(f"Built {len(rows)} ticket rows for frontend")
    return {"rows": rows, "meetingWindow": win}


@router.patch("/{ticket_id}")
def patch_ticket(ticket_id: int, body: Dict[str, Any] = Body(...)):
    """
    Updates ticket fields. Supports status and reassignment.
    If an assignee_id is provided, will automatically enrich with the user’s group_id.
    """
    allowed = {}
    if "status" in body:
        allowed["status"] = body["status"]

    if "assignee_id" in body:
        assignee_id = body["assignee_id"]
        try:
            # Look up user to auto-populate group_id
            user = zd.get_user(assignee_id)
            allowed["assignee_id"] = assignee_id
            if user and user.get("group_id"):
                allowed["group_id"] = user["group_id"]
                logger.info(f"Auto-updating group_id={user['group_id']} for reassignment to {user.get('name')}")
        except Exception as e:
            logger.warning(f"Could not enrich assignee {assignee_id} with group: {e}")
            allowed["assignee_id"] = assignee_id

    if not allowed:
        logger.info(f"No-op patch for ticket {ticket_id}")
        return {"ok": True, "noop": True}

    try:
        logger.info(f"Patching ticket {ticket_id} with {allowed}")
        t = zd.update_ticket(ticket_id, **allowed)
        return {"ok": True, "ticket": t}
    except Exception as e:
        logger.error(f"Zendesk update failed for ticket {ticket_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Zendesk update failed: {e}")

@router.post("/export")
def export_and_email(
    group_ids: Optional[str] = Query(default=None),
    statuses: Optional[str] = Query(default=None),
    ids_csv: Optional[str] = Query(default=None)
):
    logger.info("Starting export_and_email")

    # Normalize parameters
    group_ids_list = [g.strip() for g in group_ids.split(",")] if group_ids and group_ids.strip() else None
    statuses_list = [s.strip() for s in statuses.split(",")] if statuses and statuses.strip() else None

    # Pull dataset (same logic as /tickets)
    if ids_csv:
        ticket_ids = [s.strip() for s in ids_csv.split(",") if s.strip().isdigit()]
        tickets = zd.show_many(ticket_ids)
        logger.info(f"Fetched {len(tickets)} tickets via show_many for export")
    else:
        tickets = zd.search_by_groups_and_statuses(
            group_ids=group_ids_list,
            statuses=statuses_list
        )
        logger.info(f"Fetched {len(tickets)} tickets via search for export")

    status_map = zd.build_status_map(tickets)
    zd.enrich_with_resolution_times(status_map)
    win = helpers.compute_meeting_window()
    rows = helpers.build_ticket_rows(tickets, status_map, win, bucketed=True)

    # Create workbook in-memory
    wb_bytes, filename_display = helpers.make_ticket_workbook(rows)
    logger.info(f"Workbook created: {filename_display}")

    # Upload to SharePoint
    try:
        web_url = sharepoint_service.upload_bytes(filename_display, wb_bytes)
        if not web_url:
            raise Exception("Empty SharePoint webUrl")
        logger.info(f"SharePoint upload succeeded: {web_url}")
    except Exception as e:
        logger.error(f"SharePoint upload failed: {e}")
        raise HTTPException(status_code=502, detail=f"SharePoint upload failed: {e}")

    # Send email
    try:
        result = email_service.send_directors_export_link(web_url, filename_display)
        # Handle async functions or mock raising
        if hasattr(result, "__await__"):
            import asyncio
            asyncio.run(result)
        logger.info("Email notification sent successfully")
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        raise HTTPException(status_code=502, detail=f"Email send failed: {e}")


    # Write export metadata
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "filename": filename_display,
        "sharepointUrl": web_url,
        "rows": len(rows),
        "filters": {
            "group_ids": group_ids_list,
            "statuses": statuses_list,
            "ids_csv": ids_csv,
        },
    }
    _write_export_meta(meta)

    logger.info("Export and email completed successfully")

    return JSONResponse(
        status_code=200,
        content={"ok": True, "sharepointUrl": web_url, "filename": filename_display},
    )


@router.get("/", dependencies=[Depends(require_auth)])
def list_tickets_alias(
    request: Request,
    group_ids: Optional[str] = Query(default=None),
    statuses: Optional[str] = Query(default=None),
    ids_csv: Optional[str] = Query(default=None),
    bucketed: bool = True,
):
    return get_tickets(request, group_ids=group_ids, statuses=statuses, ids_csv=ids_csv, bucketed=bucketed)


@router.get("/export/last")
def get_last_export_metadata() -> Dict[str, Any]:
    """Return the last export metadata persisted after /export."""
    meta = _read_export_meta()
    if not meta:
        return {"ok": False, "detail": "No export metadata found"}
    return {"ok": True, "meta": meta}


# 🔹 NEW endpoint: list only OAPS users (for dropdowns)
@router.get("/users", response_model=Dict[str, List[User]])
def list_users():
    try:
        users = zd.list_oaps_users()  # implement in zendesk_service
        logger.info(f"Fetched {len(users)} OAPS users")
        return {"users": users}
    except Exception as e:
        logger.error(f"Failed to fetch OAPS users: {e}")
        raise HTTPException(status_code=502, detail=f"User fetch failed: {e}")
    
@router.post("/{ticket_id}/comments", response_model=Dict[str, Any])
def post_comment(ticket_id: int, comment: Comment):
    """
    Adds a comment to the specified Zendesk ticket.

    Validates payload via `Comment` schema for predictable request shape.
    Automatically respects UNIT_MODE or APP_ENV=test for mock execution.
    """
    import sys
    text = comment.body.strip()
    is_public = comment.is_public
    author_id = comment.author_id

    if not text:
        logger.warning(f"Rejected empty comment for ticket {ticket_id}")
        raise HTTPException(status_code=400, detail="Empty comment.")

    # ✅ Dynamic environment check (no global UNIT_MODE dependency)
    unit_mode = os.getenv("UNIT_MODE", "0") == "1"
    running_pytest = "pytest" in sys.modules

    if unit_mode and not running_pytest:
        logger.info(f"UNIT_MODE active — skipping live Zendesk comment for {ticket_id}")
        return {
            "ok": True,
            "ticket": {
                "id": ticket_id,
                "comment": text,
                "public": is_public,
                "author_id": author_id,
            },
        }

    # 🧩 Execute real (or mocked) Zendesk call
    try:
        logger.info(f"Adding {'public' if is_public else 'internal'} comment to ticket {ticket_id}")
        t = zd.add_comment(ticket_id, text, public=is_public)
        return {"ok": True, "ticket": t}

    except HTTPException as e:
        logger.warning(f"Zendesk returned HTTPException for {ticket_id}: {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"Zendesk comment failed for ticket {ticket_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Zendesk comment failed: {e}")


@router.get("/{ticket_id}/comments", response_model=Dict[str, Any])
def get_last_comments(ticket_id: int, limit: int = Query(default=3, ge=1, le=10)) -> Dict[str, Any]:
    """Return the last N comments for a ticket for inline display."""
    try:
        # Service call; tests may monkeypatch this
        comments = zd.get_last_comments(ticket_id, limit=limit)
        return {"ok": True, "comments": comments}
    except Exception as e:
        logger.error(f"Fetching last comments failed for ticket {ticket_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Comments fetch failed: {e}")
