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
[x] Define app parameters (BACKEND_URL, API_KEY)
[x] Add ticket_sidebar + nav_bar locations

🧩 Vanilla ZAF App
[x] index.html + SDK script
[x] index.js to init ZAFClient
[x] Display tickets from /api/tickets
[x] Status/assignee dropdowns (PATCH → FastAPI)
[x] Comments + note field integration
[x] Export trigger (SharePoint + email)
[x] CSS layout/styling

⚙️ Backend Communication Layer
[x] CORS setup for Zendesk origins
[x] /health endpoint
[x] Frontend call logging

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
 [x] Backend endpoint: GET /api/v2/tickets/{id}/comments?limit=3
 [] Show last 3 comments inline (UI)

📤 Exports
[x] /api/export → SharePoint upload
[x] "Export Tickets" button in UI
[x] Email notification post-export
 [x] Persist export metadata after /export
 [x] Backend endpoint: GET /api/v2/tickets/export/last
 [] "Last export" metadata display (UI)

✅ Deliverable for v2.0:
A fully functional Zendesk sidebar app with backend-connected ticket table, reassignment, and export capabilities - deployable in DOE sandbox via ZAT.


---

## Phase 3 Progress (backend complete)

- [x] Comments API: GET `/api/v2/tickets/{id}/comments?limit=3`
- [x] Export metadata persisted after `/export`
- [x] Export metadata API: GET `/api/v2/tickets/export/last`
- [x] Tests added (unit/integration, prefix `test_v2_3_*`)
- [x] Coverage configured (pytest-cov, 90% threshold)
- [ ] UI: show last 3 comments inline
- [ ] UI: display "Last export" metadata

## ZAT Setup & Local Preview (Phase 2)

Prep done (no ZAT required)
- [x] Add ZAT origin to sample CORS (`.env.example`)
- [x] Create `frontend/public/settings.json` for local params
- [x] Enhance `public/assets/index.js` to read ZAF params, then fall back to query (`?backend=`/`?apikey=`) or `settings.json`

Pending — requires ZAT/Ruby
- [ ] Download and install Ruby + DevKit 3.4.7-1 (x64)
- [ ] Add Ruby executables to PATH (during install)
- [ ] Run `ridk install` and select option `3` (MSYS2 toolchain)
- [ ] Verify Ruby install → `ruby -v` and `gem -v`
- [ ] Install Zendesk Apps Tools (ZAT) → `gem install zendesk_apps_tools`
- [ ] Verify ZAT CLI → `zat --version`
- [ ] Validate manifest.json → `zat validate`
- [ ] Start backend → `uvicorn backend.main:app --reload --port 8080`
- [ ] Confirm `CORS_ORIGINS=http://localhost:4567` in `.env`
- [ ] Run ZAT preview server → from `frontend/public`: `zat server --config settings.json`
- [ ] Open Zendesk agent UI preview → `https://<subdomain>.zendesk.com/agent/?zat=true`
- [ ] Verify app loads in ticket sidebar
- [ ] Test FastAPI connectivity (no CORS errors)
- [ ] Package for upload → `zat package` creates `zendesk_app.zip`
