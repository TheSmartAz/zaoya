# Known Issues (v0)

## Phase 2: Core Loop

- Version history persistence is in-memory only. Versions are lost on backend restart.
  - Status: accepted for v0/dev
  - Planned fix: persist versions in backend storage (DB or file-backed) before production

## Phase 3: Publishing

- Publish UI is implemented but not wired into the editor flow, so users cannot trigger publish yet.
  - Status: accepted for v0/dev
  - Planned fix: add publish action entry point in editor header or preview action bar

## Phase 4: Forms + Analytics

- Form submissions and analytics persistence is in-memory only. Data is lost on backend restart.
  - Status: accepted for v0/dev
  - Planned fix: persist submissions + analytics in v1 (DB-backed storage)
- Notification settings were not persisted or wired to the backend API.
  - Status: fixed in v0 follow-up
  - Planned fix: none (backend PATCH + UI wiring implemented)
- Email notification flow requires a configured `EMAIL_API_KEY` and PATCH `/api/projects/{id}` should be verified in a configured environment.
  - Status: pending verification
  - Planned fix: verify in staging/dev with email provider credentials

## Platform Persistence

- Project/user/published-page storage is in-memory only. Data is lost on backend restart.
  - Status: accepted for v0/dev
  - Planned fix: move to SQLite in v0 per SPEC-v0, then migrate to PostgreSQL in v1 per SPEC-v1

## Local Development

- Published pages host restriction can block frontend API calls when `pages_url` defaults to `http://localhost:8000`.
  - Symptom: editor requests to `localhost:8000` return 404s because that host is reserved for published pages only.
  - Status: accepted for v0/dev
  - Workaround: set `VITE_API_BASE=http://127.0.0.1:8000` (or set `pages_url` to a different host in `backend/.env`).
