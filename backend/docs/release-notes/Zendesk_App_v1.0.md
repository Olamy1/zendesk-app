# Zendesk App — v1.0 Release Notes

📅 Date: September 2025
🏷️ Tag: v1.0.0

🧭 Scope

OAPS Zendesk App Initial Release: establishes a unified Helpdesk management tool replacing fragmented workflows, static reports, and manual exports. The system allows OAPS directors and staff to view, reassign, annotate, and export tickets directly within Zendesk—modernizing bi-weekly meeting operations through real-time data access.

# 🚀 Summary

This initial release delivers the foundation for OAPS Helpdesk modernization. The Zendesk App unifies the entire case management workflow into a single interface: ticket visualization, reassignment, commenting, and exporting.

# Highlights:

  - Built with a FastAPI backend for real-time data enrichment and export.
  - Integrated ZAF-based frontend providing an intuitive ticket table view and inline editing.
  - Automated export pipeline producing the established “4-tab” workbook for recordkeeping.
  - Seamless synchronization between assignees and groups for improved data accuracy.

# Outcomes:

 `- Eliminates outdated Excel export dependency.`
 `- Reduces friction during meetings by enabling live updates.`
 `- Enables directors to annotate and act directly in Zendesk.`
 `- Aligns data consistency across OAPS teams.`

# 🔧 Core Backend (FastAPI)

📂 Modules: main.py, tickets.py, zendesk_service.py

Backend Infrastructure

# App Scaffold:

FastAPI application with CORS enabled and /health endpoint.
Environment-driven configuration for Zendesk and SharePoint integration.

# Tickets API Endpoints:

 ` - /meeting-window — defines current reporting window.`
  `- /tickets — fetches Zendesk tickets, enriches with age buckets and resolution times.`
  `- /tickets/{id} (PATCH) — updates ticket status and assignee.`
    `🔹 Enhancement: automatically syncs group_id on reassignment.`
  `- /tickets/{id}/comments — posts internal or public notes.`
 ` - /export — builds workbook, uploads to SharePoint, and emails directors.`
  `- /users — lists OAPS users (filtered via OAPS_GROUP_IDS).`

# Zendesk Service Layer

API Wrapper:

Implements retry logic, structured logging, and token masking.

Ticket operations: show_many, search_by_groups_and_statuses, update_ticket, add_comment.

Metric enrichment: get_metrics_solved_at, get_last_resolution_from_audits.

User operations: get_user, list_oaps_users (OAPS-only scope).

# System Benefits

  ✅ Standardized ticket retrieval and enrichment.
  ✅ Centralized updates and comments with error handling.
  ✅ Export automation aligned with OAPS SharePoint workflows.

# 💻 Frontend (ZAF React App)

📂 Modules: `App.jsx`, `Dashboard.jsx`, `AuditLog.jsx`, `Settings.jsx`, `useTickets.js`, `TicketTable.jsx`, `TicketRow.jsx`

# Core Interface

  ZAF Integration (zaf.js)
    - Connects to backend via parameters (BASE_URL, etc.).
    - Runs in Zendesk sidebar context.

# App Shell (App.jsx)
    - Navigation between Dashboard, Audit Log, and Settings.
    - Environment awareness (production/test).

# Dashboard View (Dashboard.jsx)
    - Displays ticket breakdowns.
    - Provides Refresh and Export actions.
    - Toggles between bucketed vs. exact age views.
    - Summary counters (>30 days, >20 days, etc.).

# Ticket Management Components

  useTickets.js (Hook):
      Fetches tickets and reporting window.
      Exposes updateStatus, reassign, addNote utilities.

  TicketTable.jsx:
      Fetches OAPS user list.
      Renders columns for ID, Subject, Assignee, Status, Age.

TicketRow.jsx:
      Inline dropdowns for Status and Assignee.
      🔹 Dynamic group sync: changing assignee updates group.
      🔹 Optimistic UI: immediate column updates pre-response.
      Editable notes and comment submission.

# Design Principles

  ✅ Fast context switching between tickets.
  ✅ Live reassignment and status updates.
  ✅ Familiar interface mirroring the “4-tab” Excel layout.

# 📊 Export & Workflow Automation

📂 Endpoint: /export

  - Generates a structured workbook replicating the Completion Monitoring layout.
  - Uploads automatically to OAPS SharePoint.
  - Sends export notifications to directors for distribution.
  - Ensures consistency with the historical Excel “4-tab” model used for years.

Result: Exports are now instantaneous, automated, and version-controlled — replacing the manual process of downloading, cleaning, and emailing Excel sheets weekly.

# 🧠 Use Case & Problem Solved

Designed For:
OAPS directors and staff who require a centralized, real-time dashboard to manage and annotate Helpdesk tickets during meetings.

# Addresses:

  Inconsistent and stale Excel exports.
  Manual reassignments not synced across teams.
  Lack of real-time group visibility.
  Inefficient meeting workflows without ticket-level notes.

# 🧩 Architecture Overview

Layer	              Technology	                       Purpose
Frontend	         ZAF SDK + React	           In-Zendesk ticket interface
Backend	                FastAPI	                 RESTful ticket management
Data Layer	      Zendesk API + SharePoint	    Source of truth & export storage
Auth & Config	      .env Environment Variables	      Secure key isolation

# 🧪 Testing & Verification 
Area	Tests Performed	                                               Outcome
API	 Ticket retrieval, PATCH updates, export validation	  ✅ Successful responses & logging
Frontend	      Dropdown actions, refresh, export	        ✅ Stable under sidebar context
Export	        Workbook structure, SharePoint upload	    ✅ 1:1 structure with legacy Excel model
📦 Deployment Checklist

Confirm .env variables:

ZENDESK_URL, ZENDESK_EMAIL, ZENDESK_TOKEN

SHAREPOINT_SITE, SHAREPOINT_PATH, EMAIL_SMTP

Validate FastAPI backend is live and accessible from Zendesk iframe.

Load app manifest in Zendesk Admin → Upload Private App.

Test app in sandbox (ticket sidebar context).

Run /export endpoint and verify SharePoint upload + email receipt.

✅ Outcome

  - Operational Efficiency: Reduced meeting prep from hours to minutes.
  - Real-Time Visibility: All tickets synchronized and editable in Zendesk.
  - Data Integrity: Group alignment and assignee sync validated.
  - Governance Ready: Consistent recordkeeping across OAPS teams.

# 🧾 Final Word

`Version 1.0 of the OAPS Zendesk App lays the groundwork for a modern, real-time support environment.`

`By unifying ticket management, reassignment, and reporting inside Zendesk, the team moves from manual maintenance to automated insight — setting the stage for future scalability, analytics, and AI-powered support in v2.0+.`