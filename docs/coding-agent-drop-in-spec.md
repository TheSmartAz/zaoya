Nice — here’s the next “drop-in spec” you can hand to your coding agent to start implementing the agent+tool loop in Zaoya **without rewriting your whole system**.

## 1) Add a Build Orchestrator (parallel to Interview v2)

### New backend module layout

```
backend/app/services/build_runtime/
  orchestrator.py
  models.py
  agents.py
  tools.py
  policies.py
  storage.py
```

### New API endpoints

* `POST /api/build/start`
* `POST /api/build/step`
* `GET  /api/build/{build_id}`
* `POST /api/build/{build_id}/abort`
* `POST /api/build/{build_id}/publish_ready` (optional gate)

**Start request**

```json
{
  "project_id": "…",
  "seed": {
    "brief": { ...ProjectBrief },
    "build_plan": { ...BuildPlan },
    "product_doc": { ...ProductDocument }
  }
}
```

**Step request**

```json
{
  "build_id": "…",
  "user_message": "…",
  "mode": "auto|plan_only|implement_only|verify_only"
}
```

---

## 2) Persist build artifacts (so the loop is replayable)

### Pydantic models (backend/app/services/build_runtime/models.py)

* `AppSpec` (structured UI/data/actions spec)
* `BuildGraph` (task DAG)
* `Task` (single implementable unit)
* `PatchSet` (unified diff + file list + rationale)
* `ValidationReport` (from your validator)
* `CheckReport` (typecheck/lint/unit)
* `QAReport` (flow runner results)
* `BuildState` (current status + pointers to latest artifacts)

**Minimum viable `Task`**

```python
class Task(BaseModel):
    id: str
    title: str
    goal: str
    acceptance: list[str]
    files_expected: list[str] = []
    depends_on: list[str] = []
    status: Literal["todo","doing","done","blocked"] = "todo"
```

**Minimum viable `PatchSet`**

```python
class PatchSet(BaseModel):
    task_id: str
    diff: str                  # unified diff
    touched_files: list[str]
    notes: str
```

Store these in DB (or in snapshots metadata first if you want speed). The key is: **don’t rely on chat history as state**.

---

## 3) Implement the tool layer (server-side, permissioned)

### Tools you need first (MVP)

**Repo**

* `repo.read(path, start_line?, end_line?)`
* `repo.search(query)`
* `repo.apply_patch(diff)`  ← use this for iteration

**Build**

* `validate.run(html, js?)` ← call your existing pipeline
* `snapshot.create(reason)`
* `snapshot.revert(snapshot_id)` (optional)

**Checks**

* `check.frontend_typecheck()`
* `check.frontend_lint()`
* `check.backend_unit()` (even if thin at first)

> Start with these. Add “flow runner” later.

### Permissions (simple matrix)

* Implementer: allow repo + snapshot + validate + checks
* Reviewer/Planner: read/search only

This single rule (“only Implementer can write”) prevents 80% of chaos.

---

## 4) Define the agents as strict I/O functions (no magic)

### Agents (backend/app/services/build_runtime/agents.py)

* `PlannerAgent`: outputs `BuildGraph`
* `ImplementerAgent`: outputs `PatchSet` (and only it triggers tool calls)
* `ReviewerAgent`: outputs `Approve|RequestChanges` with fix list

**Planner output**

* <=15 tasks max
* each task small: ≤ ~5 files touched

**Reviewer output**

* block if validator fails
* block if typecheck fails
* otherwise approve

---

## 5) The orchestration loop (deterministic state machine)

### States

`planning → implementing → verifying → reviewing → iterating → ready`

### One `step()` does:

1. if no BuildGraph: call PlannerAgent → store BuildGraph
2. pick next `todo` task → call ImplementerAgent
3. apply PatchSet via `repo.apply_patch`
4. run `validate.run` on generated output (or on changed page)
5. run checks
6. call ReviewerAgent with reports
7. mark task done or request changes

This is exactly the “Lovable/Bolt feel”: plan + small patch + verify + repeat.

---

## 6) Frontend minimal UI changes (so users can see progress)

Add a “Build Timeline” panel:

* current task title
* last PatchSet summary
* validator status
* check status
* buttons: “Revert last patch”, “Retry step”

Use your existing snapshot + diff concepts to power revert.

---

## 7) What to build first (ordered)

1. Build Orchestrator endpoints + BuildState persistence
2. PatchSet apply + snapshot after each patch
3. Verification hooks: validator + typecheck/lint
4. Reviewer gate that blocks publish unless green
5. Timeline UI panel

Once this is in, Zaoya will already feel agentic.
