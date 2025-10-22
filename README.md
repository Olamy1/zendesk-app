# OAPS Zendesk App (v2.x)

A FastAPI backend + Zendesk App Framework (ZAF v2) frontend used by DOE to review, reassign, comment on, and export Zendesk tickets.

## Features
- Versioned API (`/api/v2/*`) with schemas, unified errors, and middleware.
- Ticket table: status/assignee updates, closed-by-meeting flag, group sync.
- Comments: add new comments; fetch last 3 for inline display (Phase 3 backend).
- Export: generate workbook, upload to SharePoint, email link; last export metadata (Phase 3 backend).

## Quick Start
- Python 3.11+
- From `Zendesk_App_clean`:
  - `pip install -r backend/requirements.txt`
  - `uvicorn backend.main:app --reload --port 8080`
- Health:
  - `GET http://localhost:8080/health`
  - `GET http://localhost:8080/api/v2/health`

## Configuration
- `.env` (see `.env.example`):
  - `APP_ENV=local|test|integration|prod`
  - `DEBUG=true|false`
  - `CORS_ORIGINS=http://localhost:4567,...` (include ZAT origin for preview)
  - `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN`
  - SharePoint/Email credentials for export workflow
- Auth: Bearer tokens enforced on `/api/*` in non-local envs (TokenAuthMiddleware).
  - Set `API_AUTH_TOKEN` or `ZENDESK_API_TOKEN` for protected calls.

## API Usage (v2)
- Tickets
  - `GET /api/v2/tickets`
  - `PATCH /api/v2/tickets/{ticket_id}` body: `{ "status": "open" | "pending" | ..., "assignee_id": 123 }`
  - Comments
    - Add: `POST /api/v2/tickets/{ticket_id}/comments` body: `{ "body": "text", "is_public": true, "author_id": 123 }`
    - Last N: `GET /api/v2/tickets/{ticket_id}/comments?limit=3`
  - Export
    - Run export: `POST /api/v2/tickets/export`
    - Last export meta: `GET /api/v2/tickets/export/last`
- Users
  - `GET /api/v2/users`
- Docs
  - OpenAPI UI: `http://localhost:8080/docs`
  - ReDoc: `http://localhost:8080/redoc`

## Frontend Preview
- Without ZAT (local): open `frontend/public/assets/index.html`
  - Provide backend via `frontend/public/settings.json` or query param `?backend=http://localhost:8080`
- With ZAT (recommended):
  - Install Ruby + ZAT, then from `frontend/public`: `zat server --config settings.json`
  - Visit `https://<subdomain>.zendesk.com/agent/?zat=true`

## Testing & Coverage
- `pytest` (configured with `--cov=backend --cov-fail-under=90`)
- New Phase 3 tests are prefixed `test_v2_3_*`.

## Notes
- v1-style legacy routes exist for compatibility; prefer `/api/v2/*`.
- UI work for “last 3 comments” and “last export” display will land after ZAT preview.
