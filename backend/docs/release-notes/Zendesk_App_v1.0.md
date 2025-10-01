# =================================================================================================
# File: v1.0.md — Zendesk App Release Notes
# Description: Version 1.0 release of the OAPS Zendesk App
#
# Why it was made:
#   To replace manual, time-consuming ticket exports and static reports with a real-time,
#   interactive system that allows directors and staff to view, manage, and reassign tickets
#   directly within Zendesk during bi-weekly meetings.
#
# Benefits:
#   - Eliminates reliance on manual Excel exports and ad-hoc updates.
#   - Provides real-time syncing between assignees and groups.
#   - Centralizes ticket management, note-taking, and reporting in one tool.
#   - Improves meeting efficiency by reducing "digging" for ticket details.
#
# Use Case:
#   Designed for OAPS directors and staff who need a clear view of outstanding tickets, the
#   ability to reassign them on the fly, and automated exports that mirror the established
#   “4-tab” workbook structure for recordkeeping and distribution.
#
# Problem it Solves:
#   - Manual exports from Zendesk were inconsistent and often stale.
#   - Reassignments required multiple steps and were not reflected in real time.
#   - Group alignment with assignees was prone to errors and guesswork.
#   - Directors had no seamless way to annotate or track notes during meetings.
#
# Author: Olivier Lamy
# Version: 1.0.0 | Released: September 2025
# =================================================================================================


# ✅ Completed So Far

## 🔧 Core Backend (FastAPI)

- **App scaffolded** (`main.py`) with CORS + health check.  
- **Tickets API** (`tickets.py`):  
  - `/meeting-window` → provides current reporting window.  
  - `/tickets` → pulls tickets from Zendesk, enriches with age buckets + resolution times.  
  - `/tickets/{id}` (PATCH) → updates ticket status and assignee.  
    - 🔹 Enhancement: auto-enriches `group_id` when reassigned.  
  - `/tickets/{id}/comments` → posts public or internal notes.  
  - `/export` → builds workbook, uploads to SharePoint, emails directors.  
  - `/users` → lists OAPS-only users for dropdowns (pulled from Zendesk, filtered by env `OAPS_GROUP_IDS`).  

- **Zendesk service** (`zendesk_service.py`):  
  - Robust API wrapper with `_retry`, logging, masking for email/token.  
  - Ticket ops: `show_many`, `search_by_groups_and_statuses`, `update_ticket`, `add_comment`.  
  - Enrichment: `get_metrics_solved_at`, `get_last_resolution_from_audits`.  
  - User ops: `get_user`, `list_oaps_users` (restricted to OAPS groups).  


## 💻 Frontend (ZAF React App)

- **ZAF Integration** (`zaf.js`) → reads app parameters (like backend base URL).  
- **App.jsx** → navigation between Dashboard, Audit Log, Settings.  
- **Dashboard.jsx**:  
  - Ticket breakdown view.  
  - Refresh + Export buttons (to SharePoint/email).  
  - Age toggle (bucketed vs exact days).  
  - Summary pill counts (>30, >20, etc.).  
  - Connected to `useTickets` hook for fetching/updating tickets.  

- **AuditLog.jsx** → placeholder page (will later render `/audit-log` CSV).  
- **Settings.jsx** → placeholder (uses env + Zendesk app params).  

- **useTickets.js** → hook for tickets lifecycle:  
  - Fetches tickets + meeting window.  
  - Provides `updateStatus`, `reassign`, `addNote`.  

- **TicketTable.jsx**:  
  - Fetches OAPS users once at table-level.  
  - Passes them into each row.  
  - Renders column headers + rows.  

- **TicketRow.jsx**:  
  - Status dropdown (updates Zendesk in real time).  
  - Assignee dropdown (limited to OAPS users).  
    - 🔹 Enhancement: selecting assignee also updates `group_id` dynamically.  
    - 🔹 Optimistic UI → group column flips immediately on reassignment.  
  - Age column (bucketed or exact days).  
  - ClosedByMeeting flag.  
  - Notes editor for comments.  


## 📊 Export / Workflow

- Export includes ticket breakdown workbook.  
- Workbook is pushed to SharePoint and emailed to directors.  
- Export remains consistent with the Excel “4-tab” structure directors already use.  


## 🚀 Current State

You now have:  
- A **working frontend (ZAF widget)** that shows tickets, allows updates, reassignments, comments, and exporting.  
- A **backend** that talks to Zendesk, syncs assignees + groups, logs updates, and exports reports.  
- A **real-time reassignment system** (assignee → group sync).  

---
