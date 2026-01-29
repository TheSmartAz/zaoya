Got it — treat everything above as the **v3 build loop**. Here’s how I’d re-frame it so you can keep v2 focused and still avoid a future refactor disaster.

## What stays in v2 (now)

Keep v2 as: **Interview → single-pass generation → validate → preview → snapshot → publish**, plus a couple of tiny “prep-for-v3” hooks.

### Do these 3 prep hooks only

1. **Store artifacts explicitly**

* Save `ProjectBrief`, `BuildPlan`, `ProductDocument` as versioned JSON blobs tied to the current snapshot.
* This becomes the seed for v3 later.

2. **Introduce a PatchSet concept (even if unused)**

* Add a DB table or snapshot-metadata shape for:

  * `patch_sets: [{id, created_at, diff, touched_files, notes}]`
* You don’t need to *generate* patches yet—just define the format and surface it.

3. **Add verification “slots”**

* In your generation pipeline, add structured places to attach:

  * `ValidationReport`
  * `CheckReport` (can be empty)
* This ensures v3 can plug in checks without changing APIs.

That’s it. No orchestration yet.

---

## What becomes v3 (next build)

### v3 goals

* Multi-step “plan → implement → verify → iterate”
* Multi-agent roles
* Tool permissioning
* Patch-based iteration (not full rewrites)

### v3 deliverables (minimal but real)

1. `BuildState` + `BuildGraph` persisted
2. Implementer outputs `PatchSet` diffs
3. Apply patch → run validator → run checks
4. Reviewer blocks unsafe changes
5. Timeline UI in editor

---

## How to avoid a v3 rewrite (key interface decisions now)

If you only lock these interfaces in v2, v3 becomes additive:

### 1) Snapshot metadata shape

Attach to every snapshot:

* `brief`
* `plan`
* `product_doc`
* `reports: { validation?, checks?, qa? }`
* `patch_sets: []` (even empty)

### 2) “Build seed” contract

Define and keep stable:

```json
{
  "project_id": "...",
  "snapshot_id": "...",
  "brief": {...},
  "build_plan": {...},
  "product_doc": {...}
}
```

### 3) Diff application API (even if internal)

Have one server function that takes a unified diff and applies it to draft/snapshot.
v3 will reuse it directly.

---

## Updated roadmap wording you can hand to your coding agent

* **v2**: generator-first, stable publish, store structured artifacts + reports + empty patchsets.
* **v3**: introduce Build Orchestrator, agent roles, tools, diff-based iteration, verification loop, timeline UI.

Cool — here’s a clean **v2 → v3 bridge plan** you can paste into your repo as a single engineering note. It’s intentionally “small now, big later.”

## v2 (now): Add only the v3 scaffolding

### A) Persist structured artifacts on every snapshot

**Goal:** v3 can start from stable inputs, not chat history.

Add snapshot metadata (DB columns or a JSON table) to store:

* `brief_json` (ProjectBrief)
* `build_plan_json` (BuildPlan)
* `product_doc_json` (ProductDocument)
* `reports_json` (object)
* `patch_sets_json` (array, initially empty)

**reports_json shape (v2)**

```json
{
  "validation": { "ok": true, "errors": [], "warnings": [] },
  "checks": null,
  "qa": null
}
```

### B) Standardize a PatchSet format (even if unused)

**Goal:** v3 iteration uses diffs; v2 just defines the schema.

**PatchSet shape**

```json
{
  "id": "ps_...",
  "created_at": 0,
  "diff": "",
  "touched_files": [],
  "notes": "",
  "task_id": null
}
```

### C) Add one internal function: `apply_unified_diff(diff) → updated_files`

**Goal:** v3 will call this; v2 doesn’t need UI.

Put it in backend `services/` and make it work on your **draft snapshot** directory/model.

---

## v3 (next build): Add the agentic build loop (additive)

### v3 artifacts (persisted)

* `BuildState`
* `BuildGraph`
* `Task[]`
* `PatchSet[]`
* `ValidationReport`
* `CheckReport`
* `QAReport` (optional)

### v3 endpoints

* `POST /api/build/start`
* `POST /api/build/step`
* `GET  /api/build/{build_id}`

### v3 loop

Plan → Implement(diff) → Apply → Validate → Check → Review → Repeat.

---

## Minimal v3 UI (editor)

* “Build Timeline” panel showing:

  * current task
  * latest patch notes
  * validation + checks status
  * buttons: revert last patch / retry step

---

If you want a next step that’s super actionable: tell your coding agent to implement **only v2 scaffolding A+B+C** (artifact persistence + patchset schema + diff-apply utility). That makes the v3 build loop straightforward and avoids a rewrite.

