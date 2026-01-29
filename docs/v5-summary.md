# v5-summary

Date: 2026-01-29

## Sources
- docs/v4-summary.md (v4 baseline)
- docs/phases/v5-phase-1-foundation.md
- docs/phases/v5-phase-2-version-system.md
- SPEC-v5.md

## Overall Status
- v4 baseline complete per docs/v4-summary.md (2026-01-27).
- v5 Phase 1 (Foundation) implemented in this session; checklist below reflects current codebase.
- v5 Phase 2 (Version System) implemented; see Phase 2 checklist and notes below.
- v5 Phase 3 (Reliability) implemented; see Phase 3 checklist and notes below.
- v5 Phase 4 (Thumbnails + SEO) implemented with minor follow-ups noted below.

## Changelog
- 2026-01-28: Created v5 summary tracker with Phase 1 checklist and acceptance highlights.
- 2026-01-28: Implemented Phase 1 foundation end-to-end (Code Tab + access control, CSP/Tailwind inlining pipeline, preview/publish template separation, and owner-only enforcement with tests).
- 2026-01-28: Added publish simulation toggle in preview UI, /p-sim simulation routing, CSP reporting via /p-sim-report, and component extraction into components/.
- 2026-01-29: Implemented Phase 2 version system (versions + diffs + snapshots, version cards/history, rollback, branching isolation, per-branch quota, failed-version storage, and branch UI). Added chat message linkage for trigger_message_id and new migration for backfill + FK.
- 2026-01-29: Implemented Phase 3 reliability features (publish simulation mode, structured validation errors + ValidationCard actions, single-page retry, failed-version tracking, CSP report compatibility, default simulation preview, and cleanup loop).
- 2026-01-29: Implemented Phase 4 thumbnails + SEO (thumbnail/OG queue + workers, html2canvas fallback, SVG placeholder, SEO meta tags, OG image endpoint, favicon/robots, and queue monitoring API).

---

## Phase 1: Foundation
Status: Complete

Goals
- Provide code visibility (read-only) to project owners.
- Resolve Tailwind CDN vs CSP conflicts.
- Establish separate rendering contexts for preview vs publish.
- Set up access control boundaries.

Checklist
- [x] 1.1 Code Tab (read-only) with CodeMirror search + file tree
- [x] 1.2 Backend file APIs wired with owner-only checks
- [x] 1.3 Tailwind CSS inlining pipeline + runtime script hash
- [x] 1.4 Validation + prompt guards to block CDN/script tags
- [x] 1.5 Migration script for legacy Tailwind CDN removal
- [x] 1.6 Preview/publish templates separated and stored
- [x] 1.7 Owner-only access control + tests

Acceptance highlights
- Code files are visible to owners only; API returns 403 for non-owners.
- Preview uses loose CSP; publish uses strict CSP with inline CSS/runtime.
- Tailwind CDN is blocked at generation/validation time, and legacy HTML can be migrated.
- Preview/publish templates are version-controlled and used by render pipeline.

---

## Phase 2: Version System
Status: Complete

Goals
- Create a version per user message / AI iteration.
- Store versions efficiently (full snapshots + diffs).
- Enable version history browsing and branching.
- Support page-level rollback with confirmation.

Checklist
- [x] 2.1 Version data model (versions, snapshots, diffs, attempts; indexes; branch linkage; trigger_message_id)
- [x] 2.2 Version summary cards in chat (files/lines/tasks, preview/code actions)
- [x] 2.3 Version history panel (tree, pin, rollback, branch creation)
- [x] 2.4 Mixed snapshot storage (full window + pinned, diff for others)
- [x] 2.5 Page-level rollback (transactional, creates new version)

Acceptance highlights
- Versions are created per user action/build with change summaries and traceable to chat messages.
- Failed builds are stored separately (do not count toward quota).
- Branches are isolated by draft state (`project_pages.branch_id`) with independent version quota and auto-prune.
- Rollback UI shows per-page diff stats and skips missing pages.
- Version history supports branch selection (including “All branches” view).

---

## Phase 3: Reliability
Status: Complete

Goals
- Make preview equivalent to publish (catch CSP issues early).
- Provide detailed, actionable error information.
- Enable targeted recovery (retry a single page).
- Store failed versions for debugging.

Checklist
- [x] 3.1 Publish simulation mode (`/p-sim` + real CSP + report collection)
- [x] 3.2 Enhanced ValidationCard (structured errors, severity grouping, code navigation, fix/retry/rollback actions)
- [x] 3.3 Single-page retry endpoint + retry tracking
- [x] 3.4 Failed version storage (separate from quota) + cleanup loop

Acceptance highlights
- Preview supports publish simulation with real CSP headers, runtime/resource error capture, and report panel.
- Validation errors include path/line/excerpt/suggested fix, and can jump to Code Tab.
- Failed page retry does not trigger full rebuild; creates version or failed attempt with retry chain.
- Failed attempts are stored separately and are auto-cleaned on a 90-day loop.

---

## Phase 4: Thumbnails + SEO
Status: Mostly complete (minor follow-ups noted)

Goals
- Generate reliable thumbnails for project dashboards
- Create separate OG Images for social sharing
- Add SEO metadata tags to published pages
- Handle thumbnail failures gracefully without blocking publish

Checklist
- [x] 4.1 Thumbnail queue (table, dedup, backoff, max 2 workers/type, monitoring endpoint)
- [x] 4.2 Thumbnail/OG split with correct sizes + storage paths
- [x] 4.3 Worker logic + fallbacks (Playwright + client-side html2canvas + SVG placeholder)
- [x] 4.4 Frontend thumbnail states + retry button
- [x] 4.5 SEO tags (title/description/canonical/OG/Twitter/favicon/robots)
- [x] 4.6 OG image on-demand endpoint + post-publish queueing

Acceptance highlights
- Thumbnail generation runs asynchronously; failures never block publish.
- UI shows pending/running/done/failed states and supports one-click retry.
- OG image generation is queued after publish and can be forced via `/og-image/{project_id}/{page_id}`.
- Published HTML renders full SEO metadata with canonical URLs and favicon fallback.

Follow-ups
- Backoff sequence is 30s → 45s → 60s, but max_attempts is still 3 (60s not used unless attempts increases).

## Progress Summary (2026-01-28)
- Added Code Tab with file tree + CodeMirror read-only + search; wired to `/api/projects/{id}/files` and content endpoint.
- Added `owner_id` to projects with migration + backfill; enforced owner-only access for code APIs with tests.
- Added preview/publish templates, render helpers, CSP helpers, Tailwind inline CSS pipeline, and runtime script hashing.
- Updated publish + download pipelines to inline CSS/runtime and strip scripts; updated validation/prompt guards; added legacy migration script.
- Added /p-sim routes, preview simulation toggle in UI, CSP reporting via `/p-sim-report`, and simulation component extraction into `components/`.

## Progress Summary (2026-01-29)
- Added branch isolation and per-branch version quota with auto-prune; branch list/activate API and UI selector; branch creation from version.
- Added chat_messages + version_attempts, stored trigger_message_id for version traceability.
- Added rollback diff stats (per page) and “All branches” history view.
- Added migration 20260129_0023 to backfill version branches/labels and add trigger_message FK.
- Added publish simulation report storage in DB, runtime/resource error capture, and simulation report UI panel.
- Added structured validation details + ValidationCard actions (view code, fix, retry, rollback).
- Added project-level single-page retry endpoint and retry tracking with failed attempt recording.
- Defaulted preview to simulation mode when a project is available; background cleanup loop for failed attempts.
- Added thumbnail_jobs queue + workers, queue status endpoint, and project page thumbnail metadata in page API payloads.
- Added Playwright thumbnail/OG generation with html2canvas fallback + SVG placeholder storage.
- Added OG image endpoint with on-demand generation + post-publish queueing.
- Added SEO tags to publish template (canonical, OG, Twitter, favicon, robots) with ProductDoc-based description.
- Added static handlers for `/uploads/*` and `/favicon.ico` and storage config defaults.

Tests run (recent)
- `pytest backend/tests/test_code_access_control.py`
- `python -m unittest tests/test_version_card_emission.py`
- Phase 4 migrations applied: `alembic upgrade head`
- No automated tests run for Phase 4 changes.

## Notes
- Changelog updated with 2026-01-29 entry covering Phase 2 completion, branch isolation, trigger_message linkage, and migration backfill.
- Optional v5 file_metadata table remains unimplemented (per phase doc).
- Failed version storage uses `version_attempts` (with `validation_errors` + `retry_of`) instead of a separate `failed_versions` table; semantics match spec.
- `/api/csp-report` is a compatibility endpoint; simulation reporting uses `/p-sim-report/{project_id}`.
- `thumbnail_jobs.page_id` is not a strict FK because thumbnails reference `project_pages` while OG images use published `pages`.
