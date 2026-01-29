Cool — here’s the **single copy-paste handoff** you can drop into your coding agent. It’s written as an implementation spec with concrete files, models, endpoints, and the orchestration loop.

---

# Zaoya Build Runtime v1 (Agent + Tool Loop) — Implementation Spec

## Goal

Add a Lovable/Bolt-style **plan → patch → verify → review → iterate** build loop to Zaoya, reusing existing:

* Interview v2 outputs (`ProjectBrief`, `BuildPlan`, `ProductDocument`)
* Validator pipeline
* Snapshot/version system
* SSE streaming (optional for later)

This v1 MUST:

* persist build artifacts (not just chat logs)
* apply changes as **patches** (diffs), not full rewrites
* run verification (validator + typecheck/lint)
* block publish unless verified

---

## A) Backend: folder structure

Create:

```
backend/app/services/build_runtime/
  __init__.py
  models.py          # Pydantic artifact schemas
  storage.py         # DB persistence helpers (or JSON-in-snapshot metadata for v1)
  tools.py           # repo/snapshot/validate/check tools
  agents.py          # planner/implementer/reviewer prompts and I/O
  orchestrator.py    # deterministic state machine
  policies.py        # permissions by agent role
```

Add API routes:

```
backend/app/api/build.py
```

Wire it in `backend/app/main.py`.

---

## B) Data model (Pydantic) — backend/app/services/build_runtime/models.py

### 1) Core enums/types

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

BuildPhase = Literal["planning","implementing","verifying","reviewing","iterating","ready","aborted","error"]
TaskStatus = Literal["todo","doing","done","blocked"]
ReviewDecision = Literal["approve","request_changes"]
```

### 2) Artifacts

**Task**

```python
class Task(BaseModel):
    id: str
    title: str
    goal: str
    acceptance: List[str]
    depends_on: List[str] = []
    files_expected: List[str] = []
    status: TaskStatus = "todo"
```

**BuildGraph**

```python
class BuildGraph(BaseModel):
    tasks: List[Task]
    notes: str = ""
```

**PatchSet**

```python
class PatchSet(BaseModel):
    task_id: str
    diff: str                  # unified diff
    touched_files: List[str]
    notes: str = ""
```

**ValidationReport** (wrap existing validator output)

```python
class ValidationReport(BaseModel):
    ok: bool
    errors: List[str] = []
    normalized_html: Optional[str] = None
```

**CheckReport**

```python
class CheckReport(BaseModel):
    ok: bool
    typecheck_ok: bool = True
    lint_ok: bool = True
    unit_ok: bool = True
    logs: str = ""
```

**ReviewReport**

```python
class ReviewReport(BaseModel):
    decision: ReviewDecision
    reasons: List[str] = []
    required_fixes: List[str] = []
```

**BuildState**

```python
class BuildState(BaseModel):
    build_id: str
    project_id: str
    phase: BuildPhase = "planning"
    current_task_id: Optional[str] = None

    # Inputs
    brief: Dict = Field(default_factory=dict)
    build_plan: Dict = Field(default_factory=dict)
    product_doc: Dict = Field(default_factory=dict)

    # Artifacts
    build_graph: Optional[BuildGraph] = None
    last_patch: Optional[PatchSet] = None
    last_validation: Optional[ValidationReport] = None
    last_checks: Optional[CheckReport] = None
    last_review: Optional[ReviewReport] = None

    # Audit
    history: List[Dict] = Field(default_factory=list)  # append events: {"ts":..., "phase":..., ...}
```

---

## C) Persistence (v1: simplest safe option)

### Option 1 (fastest): store BuildState in DB table `build_runs`

Add a table:

* `id (build_id)`
* `project_id`
* `state_json` (JSON)
* `created_at`, `updated_at`

### Option 2 (temporary): store BuildState in snapshot metadata

If DB work is annoying now, store `BuildState` JSON in a “build_runs” table later. For v1, DB is strongly preferred.

Implement in `storage.py`:

* `create_build_run(project_id, seed_state) -> BuildState`
* `get_build_run(build_id) -> BuildState`
* `save_build_run(state)`

---

## D) Tool layer — backend/app/services/build_runtime/tools.py

### 1) Repo tools

Assume your draft content is in DB/snapshot pages; for v1, treat “repo” as:

* frontend files + backend files on disk (actual repo)
  OR (better for Zaoya) patch the draft snapshot pages content.

**v1 scope recommendation:** patch actual repo files for “platform features”, and patch draft snapshot for “generated app pages”.
If you want minimal: only patch draft snapshot pages (HTML) for now.

Implement:

* `repo_read(path)`
* `repo_search(query)`
* `repo_apply_patch(diff) -> {touched_files}`

  * Use a safe patch apply library or a simple unified diff applier
  * If patch fails, return error for reviewer

### 2) Validate tool (call your existing validator)

`validate_run(html, js=None) -> ValidationReport`

### 3) Checks

Implement shell calls:

* `check_frontend_typecheck()` → `pnpm -C frontend typecheck` or `npm run typecheck`
* `check_frontend_lint()` → `pnpm -C frontend lint`
* `check_backend_unit()` → `pytest -q` (or a fast subset)

Return combined `CheckReport`.

---

## E) Policies — backend/app/services/build_runtime/policies.py

Define “who can do what”:

* PlannerAgent: read/search only
* ReviewerAgent: read/search only
* ImplementerAgent: can call apply_patch + validate + checks

Enforce this in orchestrator by only executing tool calls from Implementer steps (v1: you can hardcode this rather than building a general permission engine).

---

## F) Agents — backend/app/services/build_runtime/agents.py

### 1) PlannerAgent

Input: `{brief, build_plan, product_doc}`
Output: `BuildGraph`

Rules:

* <=15 tasks
* tasks small; acceptance criteria explicit
* order by dependencies

### 2) ImplementerAgent

Input: `{state, current_task, relevant_files_snippets}`
Output: `PatchSet`

Rules:

* produce unified diff only
* touch ≤ ~5 files
* include “notes” describing what changed

### 3) ReviewerAgent

Input: `{task, patchset, validation_report, check_report}`
Output: `ReviewReport`

Rules:

* if validation fails → request_changes
* if checks fail → request_changes
* else approve

All agent prompts should be strict JSON output (no prose outside JSON) to reduce parsing failures.

---

## G) Orchestrator — backend/app/services/build_runtime/orchestrator.py

Implement:

### `start(project_id, seed) -> BuildState`

* create BuildRun row
* set phase = planning
* persist

### `step(build_id, user_message=None, mode="auto") -> BuildState`

Deterministic loop:

1. Load BuildState
2. If phase in {aborted, error, ready} → return state

**Planning**

* If `state.build_graph` is None:

  * call PlannerAgent → store BuildGraph
* pick next `todo` task (no unmet depends)
* set `current_task_id`, mark task doing
* phase = implementing

**Implementing**

* call ImplementerAgent for current task → PatchSet
* apply patch via `repo_apply_patch`
* store last_patch
* phase = verifying

**Verifying**

* run validator on affected page(s) or produced HTML
* run checks (typecheck + lint + unit, minimal)
* store reports
* phase = reviewing

**Reviewing**

* call ReviewerAgent
* if approve:

  * mark task done
  * if all tasks done → phase = ready
  * else phase = implementing (next task)
* else request_changes:

  * mark task blocked (or keep doing but set phase=iterating)
  * phase = iterating

**Iterating**

* ImplementerAgent gets reviewer required_fixes
* generate patch for fix-only scope
* apply, verify, review again

Append to `state.history` each phase transition.

Persist state at the end.

---

## H) API — backend/app/api/build.py

### Endpoints

1. `POST /api/build/start`
   Request:

```json
{ "project_id":"...", "seed": { "brief":{...}, "build_plan":{...}, "product_doc":{...} } }
```

Response: `BuildState`

2. `POST /api/build/step`
   Request:

```json
{ "build_id":"...", "user_message":"...", "mode":"auto" }
```

Response: `BuildState`

3. `GET /api/build/{build_id}`
   Response: `BuildState`

4. `POST /api/build/{build_id}/abort`
   Response: `BuildState` with `phase="aborted"`

---

## I) Frontend (minimal UI to expose the loop)

Add a panel “Build Timeline”:

* Current phase
* Current task title + acceptance list
* Last patch touched files
* Validator status (ok/errors)
* Checks status
* Reviewer decision + required fixes
* Buttons:

  * “Run Next Step”
  * “Abort”
  * “Retry Step” (calls `/step` again)
  * (optional) “Revert last patch” (v2)

Store in `buildStore.ts`:

* `buildId`
* `buildState`
* action methods

---

## J) Publish gating

Publishing endpoint must check:

* latest BuildState exists for project
* BuildState.phase == "ready"
* last_validation.ok == True
* last_checks.ok == True

If not, return 409 with reason.

---

## K) Success criteria (v1)

* A project can start a build run from brief/plan/doc
* The loop produces at least 3 tasks, applies patches, runs validator + checks
* Reviewer blocks unsafe changes
* UI shows progress and allows stepping
* Publish blocked unless ready
