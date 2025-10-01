from fastapi import APIRouter, HTTPException, Body, Query
from typing import Optional, Dict, Any
from backend.services import zendesk_service as zd
from backend.services import sharepoint_service as sp
from backend.services import email_service as mail
from backend.utils.helpers import compute_meeting_window, build_ticket_rows, make_ticket_workbook
from backend.utils.logger import get_logger

router = APIRouter()
logger = get_logger("tickets_router")


@router.get("/meeting-window")
def get_meeting_window():
    logger.info("Fetching meeting window")
    return compute_meeting_window()


@router.get("/tickets")
def get_tickets(
    group_ids: Optional[str] = Query(default=None, description="CSV of Zendesk group IDs"),
    statuses: Optional[str] = Query(default=None, description="CSV of statuses (open,pending,on-hold,solved,closed)"),
    ids_csv: Optional[str] = Query(default=None, description="CSV of explicit ticket IDs"),
    bucketed: bool = True
) -> Dict[str, Any]:
    """
    Returns enriched ticket rows for the frontend.
    """
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


@router.post("/{ticket_id}/comments")
def post_comment(ticket_id: int, body: Dict[str, Any] = Body(...)):
    text = (body.get("body") or "").strip()
    is_public = bool(body.get("public", False))
    if not text:
        logger.warning(f"Rejected empty comment for ticket {ticket_id}")
        raise HTTPException(status_code=400, detail="Empty comment.")
    try:
        logger.info(f"Adding {'public' if is_public else 'internal'} comment to ticket {ticket_id}")
        t = zd.add_comment(ticket_id, text, public=is_public)
        return {"ok": True, "ticket": t}
    except Exception as e:
        logger.error(f"Zendesk comment failed for ticket {ticket_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Zendesk comment failed: {e}")


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
    win = compute_meeting_window()
    rows = build_ticket_rows(tickets, status_map, win, bucketed=True)

    # Create workbook in-memory with your exact formatting/colors
    wb_bytes, filename_display = make_ticket_workbook(rows)
    logger.info(f"Workbook created: {filename_display}")

    # Upload to SharePoint + send email with better error handling
    try:
        web_url = sp.upload_bytes(filename_display, wb_bytes)
        logger.info(f"SharePoint upload succeeded: {web_url}")
    except Exception as e:
        logger.error(f"SharePoint upload failed: {e}")
        raise HTTPException(status_code=502, detail=f"SharePoint upload failed: {e}")

    try:
        mail.send_directors_export_link(web_url, filename_display)
        logger.info("Email notification sent successfully")
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        raise HTTPException(status_code=502, detail=f"Email send failed: {e}")

    logger.info("Export and email completed successfully")
    return {"ok": True, "sharepointUrl": web_url, "filename": filename_display}


# 🔹 NEW endpoint: list only OAPS users (for dropdowns)
@router.get("/users")
def list_users():
    try:
        users = zd.list_oaps_users()  # implement in zendesk_service
        logger.info(f"Fetched {len(users)} OAPS users")
        return {"users": users}
    except Exception as e:
        logger.error(f"Failed to fetch OAPS users: {e}")
        raise HTTPException(status_code=502, detail=f"User fetch failed: {e}")
