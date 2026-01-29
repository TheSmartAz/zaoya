# v3-summary

Date: 2026-01-26

## Scope
Implemented Phase 1 build runtime foundation aligned to the current repo patterns (Postgres + SQLAlchemy ORM + FastAPI DI).
Implemented Phase 2 tool layer (repo/validate/check/snapshot tools) plus frontend lint/typecheck tooling and fixes to pass checks.
Implemented Phase 3 agents and Phase 4 orchestrator state machine with agent usage tracking and validation constraints.
Implemented Phase 7 intent detection with AI-first classification and project chat-driven interview flow.

## Completed
- Added build runtime module skeleton and Pydantic models for build state/artifacts.
- Added BuildRun ORM model and Alembic migration for `build_runs` (UUID + JSONB).
- Implemented async BuildStorage for persistence plus full BuildOrchestrator flow (start/step/abort).
- Added build API endpoints (`/api/build/*`) and wired router into FastAPI app.
- Ran Alembic migration to create `build_runs`.
- Added Phase 2 tool layer implementations (RepoTools, ValidateTools, CheckTools, SnapshotTools).
- Added `validate_html` and wired validator pipeline to reuse it.
- Added snapshot service facade (`get_snapshot_service`) for tool usage.
- Added tool-layer unit tests.
- Added frontend `lint` and `typecheck` scripts, ESLint config, and resolved lint/typecheck errors.
- Removed platform-specific Rollup packages and regenerated frontend lockfile.
- Implemented Planner/Implementer/Reviewer agents with JSON parsing and prompts.
- Added agent factories and wired agent usage tracking (token counts) into BuildState/history/API response.
- Implemented full orchestrator phase logic (plan, implement, verify, review, iterate) with draft-page validation.
- Added model-level validation for BuildGraph tasks and files.
- Added unit tests for agents, orchestrator transitions, and model validation.
- Added migration for build_run agent usage tracking.
- Implemented Phase 5 frontend timeline UI (store + components) and integrated it into the editor layout with collapse behavior.
- Wired interview finish flow to start build runs and added build state refresh on reload.
- Updated `/api/projects` to create DB-backed projects (UUIDs) and auto-create dev user when auth bypass is enabled.
- Implemented Phase 6 settings backend API and stored user preferences in `User.preferences.settings`.
- Added settings store + Settings page (tabs for language, model, design defaults, notifications, account) and routed `/settings` with sidebar navigation.
- Added lightweight UI primitives (tabs, switch, select) and a PageLayout shell for non-editor pages.
- Wired preferred model/language settings into interview/chat requests and merged default design system into build plans on generation.
- Added AI intent detection with keyword fallback and inferred field extraction.
- Added interview state persistence (DB + memory fallback) and project chat SSE API to drive all interview steps.
- Routed interview flow through `/api/projects/{project_id}/chat` and removed `/api/interview/v2`.
- Added interview flow tests (project chat SSE, multi-step actions) and intent accuracy suite (>=90%).
- Added local pytest plugin suppression stubs for langsmith incompatibility.

## Files Added
- `backend/app/services/build_runtime/__init__.py`
- `backend/app/services/build_runtime/models.py`
- `backend/app/services/build_runtime/storage.py`
- `backend/app/services/build_runtime/orchestrator.py`
- `backend/app/services/build_runtime/tools.py`
- `backend/app/services/build_runtime/agents.py`
- `backend/app/services/build_runtime/policies.py`
- `backend/app/models/db/build_run.py`
- `backend/app/api/build.py`
- `backend/alembic/versions/20260125_0010_create_build_runs_table.py`
- `backend/app/services/build_runtime/repo_tools.py`
- `backend/app/services/build_runtime/validate_tools.py`
- `backend/app/services/build_runtime/check_tools.py`
- `backend/app/services/build_runtime/snapshot_tools.py`
- `backend/tests/test_build_runtime_tools.py`
- `backend/tests/test_build_runtime_agents.py`
- `backend/tests/test_build_runtime_orchestrator.py`
- `backend/tests/test_build_runtime_models.py`
- `backend/alembic/versions/20260125_0011_add_build_run_agent_usage.py`
- `frontend/.eslintrc.cjs`
- `frontend/src/vite-env.d.ts`
- `frontend/src/stores/buildStore.ts`
- `frontend/src/components/build/BuildTimeline.tsx`
- `frontend/src/components/build/TaskList.tsx`
- `frontend/src/components/build/CurrentTaskCard.tsx`
- `frontend/src/components/build/PatchSummary.tsx`
- `frontend/src/components/build/VerificationStatus.tsx`
- `frontend/src/components/build/ReviewStatus.tsx`
- `frontend/src/components/build/BuildControls.tsx`
- `frontend/src/components/ui/badge.tsx`
- `frontend/src/components/ui/select.tsx`
- `frontend/src/components/ui/switch.tsx`
- `frontend/src/components/ui/tabs.tsx`
- `frontend/src/components/layout/PageLayout.tsx`
- `frontend/src/components/settings/SettingsPage.tsx`
- `frontend/src/components/settings/LanguageSection.tsx`
- `frontend/src/components/settings/ModelSection.tsx`
- `frontend/src/components/settings/DesignSection.tsx`
- `frontend/src/components/settings/NotificationSection.tsx`
- `frontend/src/components/settings/AccountSection.tsx`
- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/stores/settingsStore.ts`
- `RUN_BACKEND_DEV.md`
- `backend/app/api/settings.py`
- `backend/app/services/intent_detection.py`
- `backend/app/services/interview_storage.py`
- `backend/app/api/project_chat.py`
- `backend/app/models/db/interview_state.py`
- `backend/alembic/versions/20260126_0012_add_interview_states_table.py`
- `backend/tests/test_intent_detection.py`
- `backend/tests/test_intent_detection_accuracy.py`
- `backend/tests/test_chat_intent.py`
- `backend/tests/test_project_chat_flow.py`
- `pytest.ini`
- `sitecustomize.py`
- `langsmith/__init__.py`
- `langsmith/pytest_plugin.py`

## Files Updated
- `backend/app/models/db/__init__.py`
- `backend/alembic/env.py`
- `backend/app/main.py`
- `backend/app/services/validator.py`
- `backend/app/services/snapshot_service.py`
- `backend/app/services/build_runtime/tools.py`
- `backend/app/services/build_runtime/agents.py`
- `backend/app/services/build_runtime/orchestrator.py`
- `backend/app/services/build_runtime/models.py`
- `backend/app/services/build_runtime/storage.py`
- `backend/app/api/build.py`
- `backend/app/services/ai_service.py`
- `backend/app/models/db/build_run.py`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/components/chat/ChatPanel.tsx`
- `frontend/src/components/chat/MessageList.tsx`
- `frontend/src/components/ui/resizable.tsx`
- `frontend/src/components/layout/EditorLayout.tsx`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/index.ts`
- `frontend/src/App.tsx`
- `frontend/src/pages/EditorPage.tsx`
- `frontend/src/stores/index.ts`
- `frontend/src/stores/projectStore.ts`
- `backend/app/api/projects.py`
- `backend/app/main.py`
- `backend/app/api/interview.py`
- `backend/app/models/schemas/interview.py`
- `backend/app/services/interview_orchestrator.py`
- `backend/app/models/user.py`
- `docs/PROJECT_SUMMARY.md`

## Migration Applied
- `alembic upgrade head` (run from `backend/`)
  - `20260125_0011_add_build_run_agent_usage`
  - `20260126_0012_add_interview_states_table`

## Notes
- Orchestrator performs plan → implement → verify → review → iterate and records agent usage per step.
- Verification loads draft pages via DraftService and runs validation/checks concurrently.
- API endpoints enforce project/user access using existing repo patterns.
- Build IDs, project IDs, and user IDs are UUID strings.
- Lint/typecheck now pass locally after typing cleanup and ESLint config adjustments.
- Snapshot tool facade resolves project owner from DB; `metadata` is currently unused by snapshot schema.
- BuildGraph validation enforces <=15 tasks (no minimum) and <=5 files per task; invalid outputs are rejected.
- Project chat endpoint now owns the full interview flow (SSE), including intent detection on first message.

## Pending (Next Phases)
- Expand tests for models/storage/API endpoints beyond tool layer.
