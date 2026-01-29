Below is a concrete blueprint for adding **Lovable/Bolt-style agent + tool orchestration** to Zaoya, using what you already have (Interview v2 → BuildPlan/ProductDoc → HTML → Validator → Preview → Snapshot/Publish). I’m going to focus on **mobile-first “app-like” experiences**, where Zaoya must manage UI + simple state + backend endpoints safely.

---

## 0) What you’re missing today (gap)

Right now Zaoya is strongest at **single-pass page generation**. To feel like Lovable/Bolt, you need:

1. **A structured build loop** (plan → implement → verify → iterate)
2. **Tooling that can actually “do work”** (write files, patch diffs, run checks, simulate user flows)
3. **A multi-agent division of labor** so requirements, UX, data, UI, and security don’t get muddled into one prompt
4. **A safer representation than raw HTML** for repeated edits (so “change X” is reliable)

You already have SSE chat, snapshots, and validation—perfect foundations.

---

## 1) Agent system design (the minimum set that works)

Think in **roles** (agents) with clear inputs/outputs, not “smart prompts”.

### 1.1 Core agents

**A) ProductBrief Agent (Requirements)**

* Input: InterviewState + user last message + current ProjectBrief
* Output: `BriefPatch` (JSON Patch) + `OpenQuestions[]` (if needed)

**B) UX Agent (Mobile UX / IA)**

* Input: ProjectBrief + current UI spec
* Output: `UXSpec` (navigation, screens, empty states, error states, microcopy)

**C) Data/Domain Agent**

* Input: ProjectBrief + UXSpec
* Output: `DataModelSpec` (entities, fields, validation rules), plus “what must live on server vs client”

**D) Build Planner Agent**

* Input: Brief + UXSpec + DataModelSpec
* Output: `BuildGraph` (tasks with dependencies) + file-level plan

**E) Implementer Agent (CodeGen)**

* Input: next task from BuildGraph + repo state
* Output: `PatchSet` (diff) + “why” notes + follow-up tasks

**F) Reviewer Agent (Security/Quality)**

* Input: PatchSet + validator report + lint/test outputs
* Output: `Approve | RequestChanges` + targeted fixes list

**G) QA Agent (Flow Testing)**

* Input: UXSpec + current build
* Output: “simulate flows” checklist + tool calls to validate (see Tools)

> You can merge B+C early if you want fewer moving parts, but keep **Reviewer** separate. That separation is what prevents “ship unsafe code because it works.”

### 1.2 Optional “power agents” (add later)

* **Accessibility/Performance Agent** (mobile a11y + lighthouse-ish checks)
* **Copy/Brand Agent** (tone, microcopy consistency)
* **Template Curator Agent** (picks/adjusts templates based on intent)

---

## 2) Tools Zaoya needs (and how they map to your existing pipeline)

You already have a security validator that blocks network/storage primitives. That means “app-like” behavior must be implemented through **Zaoya-owned runtime helpers + your backend**.

### 2.1 Essential tools (start here)

**Repo Tools**

* `repo.read(path, range?)`
* `repo.search(query)`
* `repo.write(path, content)`
* `repo.patch(diff)` (preferred over write for iteration)

**Build Tools**

* `preview.render(snapshot_id|html)` → returns sanitized HTML + runtime JS bundle refs
* `validate.run(html, js)` → your existing validator (Stage 1–4)
* `snapshot.create()` / `snapshot.restore()`

**Backend Tools**

* `api.add_endpoint(spec)` → generates FastAPI route + Pydantic schema stub + service stub
* `db.migration.generate()` → Alembic revision template (even if you keep SQLite now)

**QA Tools**

* `check.typecheck()` (TS)
* `check.lint()` (ESLint)
* `check.unit()` (backend pytest / frontend vitest)
* `check.flow(script)` (headless “flow runner” described below)

### 2.2 “Flow runner” tool (the Lovable/Bolt secret sauce)

You need a simple internal tool that can:

* load the sandboxed preview
* click elements by data-testid
* input text
* assert UI changes / toast appears
* capture console errors

Call it: `qa.run_flow(flowSpec)`.

This turns “does it work?” into something agent-verifiable, so iterations converge.

---

## 3) The orchestration loop (how everything gets coordinated)

Implement a **Build Orchestrator** service (parallel to your interview orchestrator) that runs a deterministic state machine.

### 3.1 State machine

`idle → planning → implementing → verifying → iterating → ready_to_publish`

Each transition stores artifacts in DB (or snapshot metadata):

* `AppSpec` (structured)
* `BuildGraph`
* `PatchSets[]`
* `ValidationReports[]`
* `QAReports[]`

### 3.2 One turn of the loop

1. **Plan step**

   * Planner Agent produces next task(s) with acceptance criteria
2. **Implement step**

   * Implementer Agent uses tools to patch files
3. **Verify step**

   * run `validate.run` + `check.*` + (optional) `qa.run_flow`
4. **Review step**

   * Reviewer Agent approves or gives fix list
5. If not approved, repeat with narrower task scope

Key rule: **Only the Implementer can write.** Everyone else reads + critiques. This single rule improves stability a lot.

---

## 4) Move from “raw HTML generation” to a safer intermediate representation

Raw HTML is hard to edit reliably. For app-like experiences, introduce a tiny intermediate spec:

### 4.1 Zaoya UI Spec (ZUI)

A JSON schema like:

```json
{
  "screens": [
    {
      "id": "home",
      "route": "/",
      "title": "Home",
      "layout": [
        { "type": "header", "props": {...} },
        { "type": "card", "children": [...] },
        { "type": "form", "action": "server:CreateItem", "fields": [...] }
      ]
    }
  ],
  "actions": {
    "CreateItem": { "type": "server", "endpoint": "POST /api/items" }
  }
}
```

Then build:

* `zui.compile_to_html(zui)` → generates your Tailwind HTML + `Zaoya.*` calls
* Validator runs on the output as usual

This gives you:

* stable diffs (JSON patches)
* easier “change layout” edits
* safer constraints (you can ban certain nodes)

You don’t have to migrate everything at once. Start by representing **forms + lists + navigation** in ZUI first.

---

## 5) Make “app-like” features possible under your security model

Given your restrictions (no fetch, no storage APIs), the pattern should be:

### 5.1 All data-changing actions go through Zaoya runtime

Keep `Zaoya.submitForm`, but evolve it into a general RPC-like primitive:

* `Zaoya.action(name, payload)`
* The runtime sends to **your own backend** only (same origin on pages domain)
* Backend validates auth + schema + rate limits

This avoids opening generic network access while still enabling real interactions.

### 5.2 Server-generated endpoints are part of the build graph

If the user wants behavior that needs persistence:

* Data/Domain Agent declares entity + endpoint needs
* Planner schedules “Create endpoint + migration + service”
* Implementer uses `api.add_endpoint` tool
* QA verifies with `qa.run_flow`

---

## 6) Folder / code organization changes (so it stays maintainable)

### 6.1 Backend

Add:

* `services/agent_runtime/`

  * `orchestrator.py` (state machine)
  * `registry.py` (agents, tools)
  * `policies.py` (who can do what)
  * `artifacts.py` (schemas: AppSpec, BuildGraph, PatchSet, Reports)

* `services/tools/`

  * `repo_tools.py`
  * `build_tools.py`
  * `qa_tools.py`
  * `api_codegen_tools.py`

### 6.2 Frontend

Add:

* `stores/buildStore.ts` (build loop artifacts + statuses)
* a “Build Timeline” panel (shows tasks, patches, reports)
* “Apply patch / revert patch” UX built on your snapshot system

---

## 7) A practical “Phase 1” implementation plan (small but powerful)

If you want this to land fast without exploding scope:

1. **Introduce Build Orchestrator API**

   * `POST /api/build/start`
   * `POST /api/build/step`
   * `GET /api/build/{id}/status`

2. **Add PatchSet pipeline**

   * Implementer returns unified diff
   * Backend applies diff to draft snapshot
   * Validator runs automatically
   * Store `ValidationReport`

3. **Add QA minimum**

   * typecheck + lint
   * console-error capture from preview iframe

4. **Add Reviewer agent**

   * blocks publish if validator or checks fail

This alone will make Zaoya feel much more like an “agentic builder” rather than a generator.

---

## 8) What “good orchestration” looks like in practice (rules)

These rules keep the system stable:

* **Small tasks**: one patch set should be ≤ ~5 files
* **Always verify after write**: validation + typecheck at minimum
* **Prefer patch over rewrite**: use diffs, keep edits local
* **No new primitives without policy**: any new runtime capability must be whitelisted + validated
* **Artifacts are the truth**: UI spec / build graph / reports are persisted and replayable

---
