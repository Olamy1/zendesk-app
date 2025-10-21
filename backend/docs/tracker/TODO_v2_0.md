# Zendesk App — Multi-Phase Roadmap
Version 2.0 — App Infrastructure & MVP

Branch: v2.0_app_infra
Goal: Establish a functional, secure baseline app with backend + frontend wiring.
Target Outcome: Internal pilot-ready Zendesk app (ticket view + real-time updates).

🧩 Phase 1 — Core Infrastructure & Environment

🥇 Priority: Highest

🔐 Environment Setup
[x] Create dedicated v2.0_app_infra branch
[x] Remove legacy secrets and rebuild clean repo
[x] Validate .env structure and .gitignore rules
[x] Add config.py with dotenv integration
[x] Create .env.example for onboarding

⚙️ Backend Core Hardening
[✅] API schemas for Ticket, User, Comment
[✅] Unified error handling
[✅] Versioned routes (/api/v2/...)
[x] Structured logging and secret masking
[] Rate limiting / token validation
[x] API unit test suite

🧱 Docs & Configuration
[] /docs/release-notes/Zendesk_App_v2.0.md
[] README.md API usage section
[] OpenAPI documentation link (FastAPI auto-docs)

🖥️ Phase 2 — Frontend Integration (ZAF + Backend)

🥇 Priority: High

🪶 ZAF Manifest & Setup
[x] manifest.json SDK v2.0
[] Define app parameters (BACKEND_URL, API_KEY)
[x] Add ticket_sidebar + nav_bar locations

🧩 Vanilla ZAF App
[] index.html + SDK script
[] index.js to init ZAFClient
[x] Display tickets from /api/tickets
[x] Status/assignee dropdowns (PATCH → FastAPI)
[x] Comments + note field integration
[x] Export trigger (SharePoint + email)
[x] CSS layout/styling

⚙️ Backend Communication Layer
[x] CORS setup for Zendesk origins
[] /health endpoint
[] Frontend call logging

📊 Phase 3 — MVP Feature Delivery

🥈 Priority: Medium

📋 Ticket Table
[x] Display ID, Subject, Assignee, Status, Group, Age
[x] Inline updates (status, assignee)
[x] Auto group sync
[x] Closed-by-Meeting flag

💬 Comments & Notes
[x] Add comment input
[x] Post to /api/tickets/{id}/comments
[] Show last 3 comments inline

📤 Exports
[x] /api/export → SharePoint upload
[x] "Export Tickets" button in UI
[x] Email notification post-export
[] “Last export” metadata display

✅ Deliverable for v2.0:
A fully functional Zendesk sidebar app with backend-connected ticket table, reassignment, and export capabilities — deployable in DOE sandbox via ZAT.
