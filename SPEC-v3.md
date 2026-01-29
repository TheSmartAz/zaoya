# Zaoya (造鸭) - v3 Specification

> **"Describe what you want. We'll ask just enough questions to build it perfectly."**

v3 simplifies the onboarding by removing template selection and introduces an agentic build loop for iterative development.

---

## Vision v3

**North Star**: "Zero friction start with intelligent conversation, iterative agentic building."

v3 removes the template decision and adds intelligent iteration:

- **No template selection page** - Skip straight to conversation
- **Intent detection** - AI detects intent from user's first message
- **Adaptive interview** - Template-agnostic questions based on detected intent
- **Build Orchestrator** - Plan → Implement → Verify → Review → Iterate loop
- **Settings page added** - Centralized language and preferences

---

## What Changed from v2

| v2 Feature | v3 Change | Rationale |
|------------|-----------|-----------|
| Template selection page (/create) | **Removed** | Reduces decision paralysis; AI infers from conversation |
| Pre-filled template forms | **Removed** - Input via chat only | More flexible, natural |
| Interview (adaptive) | **Kept** - Enhanced | Core value prop, now template-agnostic |
| Single-pass generation | **Replaced** - Iterative build loop | Agentic iteration like Lovable/Bolt |
| Build plan preview | **Kept** - Enhanced with BuildGraph | Users see tasks and progress |
| Product document | **Kept** | Shows understanding before generation |
| Agent callouts | **Kept** | Visual feedback on AI's thinking |
| Language in chat header | **Moved to Settings** | Cleaner UI |
| Model selector in header | **Moved to Settings** | Cleaner UI |

---

## Core Loop (v3)

```
[User Opens App] → [Types First Message] → [AI Detects Intent + Starts Interview]
         ↓                   ↓                              ↓
    Empty state        Natural conversation       Adaptive questions (2-15)
    with prompt        (no template grid)         based on detected intent
                                                           ↓
                                             [Build Plan + BuildGraph]
                                                           ↓
                                             [User Approves/Edits]
                                                           ↓
                              ┌────────────────────────────┴────────────────────────────┐
                              ↓                            ↓                            ↓
                     [Planning Phase]            [Implementation Phase]         [Review Phase]
                              ↓                            ↓                            ↓
                     PlannerAgent creates              ImplementerAgent           ReviewerAgent
                     BuildGraph with tasks             creates PatchSet            validates
                              ↓                            ↓                            ↓
                        ┌─────────────┐           ┌─────────────────┐          ┌────────────┐
                        │ Verify step │←─────────│  Apply Patch    │────────→│ Iterating  │
                        │ (validation │           │  → Validate     │          │ (if needed)│
                        │  + checks)  │           │  → Run checks   │          └────────────┘
                        └─────────────┘           └─────────────────┘                 ↓
                                   └─────────────────────┘                           │
                                              ↓                                All tasks done
                                         [Ready to Publish]                         or approved
```

### Phase Comparison

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              v2 Flow (Single-Pass)                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   1. /create     → [Template Grid] Select from 4 categories                    │
│   2. /create     → [Template Form] Fill structured inputs                      │
│   3. /editor     → [Interview] AI asks 2-6 follow-up questions                 │
│   4. /editor     → [Build Plan] Show and approve                               │
│   5. /editor     → [Generate] AI generates full code                           │
│   6. /editor     → [Iterate] Refine via chat (full rewrites)                   │
│                                                                                 │
│   Friction: Template decision + form filling; iteration = full rewrites        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              v3 Flow (Agentic Loop)                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   1. /new        → [Empty Editor] "What do you want to create?"                │
│   2. /editor     → [User Types] "I need a wedding RSVP..."                     │
│   3. /editor     → [AI Detects] Event invitation → Starts interview             │
│   4. /editor     → [Interview] 2-6 adaptive questions based on intent          │
│   5. /editor     → [Build Plan + BuildGraph] Show tasks and approve            │
│   6. /editor     → [Build Orchestrator]                                         │
│                    ├─ PlannerAgent → BuildGraph (5-15 tasks)                    │
│                    ├─ ImplementerAgent → PatchSet (small diffs)                 │
│                    ├─ Verify → validation + checks                              │
│                    ├─ ReviewerAgent → approve or request changes                │
│                    └─ Iterate → repeat until ready                              │
│   7. /editor     → [Iterate] Refine via chat (small targeted patches)          │
│                                                                                 │
│   Friction: NONE - start typing immediately; iteration = targeted patches      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part A: Interview Flow (Template-Agnostic)

### New Entry Experience

#### 1. Landing Page (/)

Clean landing with single CTA - no template categories shown:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                              Zaoya 造鸭                                         │
│                         Describe it. See it. Share it.                          │
│                                                                                 │
│    ┌─────────────────────────────────────────────────────────────────────┐     │
│    │                                                                     │     │
│    │   What do you want to create today?                                │     │
│    │   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │     │
│    │                                                                     │     │
│    │   Tell me what you need - a landing page, portfolio,               │     │
│    │   event invitation, or anything else. I'll ask a few               │     │
│    │   questions to make it perfect.                                    │     │
│    │                                                                     │     │
│    │   ┌─────────────────────────────────────────────────────────────┐ │     │
│    │   │ I need a...                                              │ │     │
│    │   │                                                     [Start →]│ │     │
│    │   └─────────────────────────────────────────────────────────────┘ │     │
│    │                                                                     │     │
│    └─────────────────────────────────────────────────────────────────────┘     │
│                                                                                 │
│                                    [Sign In]                                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### 2. Empty Editor (/new)

No template grid. Just a prompt to start:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Zaoya                                            [Settings] [User ▾]          │
├─────────────────────────────────────────┬───────────────────────────────────────┤
│  Chat                                    │  Preview                               │
│                                          │                                       │
│  ┌─────────────────────────────────────┐│  ┌─────────────────────────────────┐ │
│  │                                     ││  │                                 │ │
│  │   What do you want to create?       ││  │         ┌─────────────┐         │ │
│  │                                     ││  │         │             │         │ │
│  │   Describe your project in a few   ││  │         │   Preview   │         │ │
│  │   words, and I'll ask some         ││  │         │             │         │ │
│  │   questions to make it perfect.    ││  │         │   Empty     │         │ │
│  │                                     ││  │         │             │         │ │
│  │   ┌─────────────────────────────┐  ││  │         │             │         │ │
│  │   │ I need a wedding RSVP page  │  ││  │         └─────────────┘         │ │
│  │   │ for Emma and John...        │  ││  │                                 │ │
│  │   └─────────────────────────────┘  ││  │                                 │ │
│  │                                     ││  │                                 │ │
│  │                              [Send]  ││  │                                 │ │
│  └─────────────────────────────────────┘│  └─────────────────────────────────┘ │
│                                          │                                       │
└─────────────────────────────────────────┴───────────────────────────────────────┘
```

### Intent Detection Categories

Instead of template selection, AI detects intent from first message:

| Detected Intent | Trigger Keywords | Question Focus |
|-----------------|------------------|----------------|
| **Event Invitation** | wedding, birthday, party, RSVP, invitation | When, where, RSVP deadline, dress code |
| **Landing Page** | landing, SaaS, product, launch, marketing | Value prop, target audience, CTA, features |
| **Portfolio/Profile** | portfolio, about me, link in bio, personal | Name, bio, links, projects, social |
| **Contact/Lead Form** | contact, lead capture, signup, inquiry | Form fields, notification email, purpose |
| **E-commerce** | shop, store, product, sell, buy, price | Products, pricing, payment, shipping |
| **Blog/Content** | blog, article, news, content, posts | Topics, author info, commenting |
| **Dashboard/App** | dashboard, admin, app, tool, portal | Data sources, features, authentication |
| **Other** | (fallback) | Open questions to understand intent |

---

## Part B: Build Orchestrator (Agentic Loop)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Build Orchestrator                                     │
│                    backend/app/services/build_runtime/                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐│
│  │  Planner    │  │ Implementer │  │  Reviewer   │  │    Tool Layer          ││
│  │  Agent      │  │   Agent     │  │   Agent     │  │  - repo_tools          ││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │  - validate_tools      ││
│         │                │                │         │  - check_tools         ││
│         └────────────────┼────────────────┘         │  - snapshot_tools      ││
│                          │                          └─────────────────────────┘│
│                          ↓                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                        State Machine                                        ││
│  │  planning → implementing → verifying → reviewing → iterating → ready       ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                          │                                                       │
│                          ↓                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                        Persistence                                          ││
│  │  - BuildState    - BuildGraph    - Task[]    - PatchSet[]                  ││
│  │  - ValidationReport[] - CheckReport[] - ReviewReport[]                     ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Folder Structure

```
backend/app/services/build_runtime/
  __init__.py
  models.py              # Pydantic schemas: BuildState, BuildGraph, Task, PatchSet, etc.
  storage.py             # DB persistence for build artifacts
  tools.py               # repo_read, repo_apply_patch, validate, check tools
  agents.py              # PlannerAgent, ImplementerAgent, ReviewerAgent prompts
  orchestrator.py        # Deterministic state machine
  policies.py            # Permission rules per agent role
```

### Data Models (Pydantic)

```python
# backend/app/services/build_runtime/models.py

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime

# === Enums ===

BuildPhase = Literal[
    "planning",      # PlannerAgent creating BuildGraph
    "implementing",  # ImplementerAgent creating patches
    "verifying",     # Running validation + checks
    "reviewing",     # ReviewerAgent evaluating
    "iterating",     # Making fixes based on review
    "ready",         # All tasks complete + approved
    "aborted",       # User stopped the build
    "error"          # Something went wrong
]

TaskStatus = Literal["todo", "doing", "done", "blocked"]

ReviewDecision = Literal["approve", "request_changes"]

# === Core Artifacts ===

class Task(BaseModel):
    """Single implementable unit of work."""
    id: str
    title: str
    goal: str
    acceptance: List[str]           # Acceptance criteria
    depends_on: List[str] = []      # Task IDs that must complete first
    files_expected: List[str] = []  # Files this task should touch
    status: TaskStatus = "todo"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class BuildGraph(BaseModel):
    """Plan of all tasks with dependencies."""
    tasks: List[Task]
    notes: str = ""                  # Planner notes
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PatchSet(BaseModel):
    """Unified diff with metadata."""
    id: str
    task_id: str
    diff: str                        # Unified diff format
    touched_files: List[str]         # Files modified
    notes: str = ""                  # What changed and why
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationReport(BaseModel):
    """Result from validator pipeline."""
    ok: bool
    errors: List[str] = []
    warnings: List[str] = []
    normalized_html: Optional[str] = None
    js_valid: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CheckReport(BaseModel):
    """Result from typecheck, lint, and unit tests."""
    ok: bool
    typecheck_ok: bool = True
    lint_ok: bool = True
    unit_ok: bool = True
    logs: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewReport(BaseModel):
    """ReviewerAgent decision with reasoning."""
    decision: ReviewDecision
    reasons: List[str] = []                 # Why this decision
    required_fixes: List[str] = []          # If request_changes
    blocked_by: List[str] = []              # Task IDs blocking
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BuildHistoryEvent(BaseModel):
    """Single event in build history."""
    ts: datetime = Field(default_factory=datetime.utcnow)
    phase: BuildPhase
    action: str                             # What happened
    details: Dict = Field(default_factory=dict)


# === Main State ===

class BuildState(BaseModel):
    """Complete build run state - the source of truth."""
    build_id: str
    project_id: str
    user_id: str
    phase: BuildPhase = "planning"
    current_task_id: Optional[str] = None

    # === Inputs (from Interview v2) ===
    brief: Dict = Field(default_factory=dict)       # ProjectBrief
    build_plan: Dict = Field(default_factory=dict)  # BuildPlan
    product_doc: Dict = Field(default_factory=dict) # ProductDocument

    # === Artifacts ===
    build_graph: Optional[BuildGraph] = None
    patch_sets: List[PatchSet] = []
    last_patch: Optional[PatchSet] = None

    validation_reports: List[ValidationReport] = []
    last_validation: Optional[ValidationReport] = None

    check_reports: List[CheckReport] = []
    last_checks: Optional[CheckReport] = None

    review_reports: List[ReviewReport] = []
    last_review: Optional[ReviewReport] = None

    # === History ===
    history: List[BuildHistoryEvent] = []

    # === Timestamps ===
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    @property
    def is_terminal(self) -> bool:
        """Check if build is in a terminal state."""
        return self.phase in {"ready", "aborted", "error"}

    @property
    def all_tasks_done(self) -> bool:
        """Check if all tasks are complete."""
        if not self.build_graph:
            return False
        return all(t.status == "done" for t in self.build_graph.tasks)

    def get_current_task(self) -> Optional[Task]:
        """Get the current task being worked on."""
        if not self.build_graph or not self.current_task_id:
            return None
        for task in self.build_graph.tasks:
            if task.id == self.current_task_id:
                return task
        return None

    def get_blocked_tasks(self) -> List[Task]:
        """Get tasks blocked by unmet dependencies."""
        if not self.build_graph:
            return []
        done_ids = {t.id for t in self.build_graph.tasks if t.status == "done"}
        blocked = []
        for task in self.build_graph.tasks:
            if task.status == "todo":
                deps_not_done = [d for d in task.depends_on if d not in done_ids]
                if deps_not_done:
                    blocked.append(task)
        return blocked
```

### Agents (backend/app/services/build_runtime/agents.py)

#### 1. PlannerAgent

**Input:**
```python
{
    "brief": {...},           # ProjectBrief
    "build_plan": {...},      # BuildPlan
    "product_doc": {...},     # ProductDocument
    "constraints": {...}      # Zaoya platform constraints
}
```

**Output:** `BuildGraph` with 5-15 tasks

**System Prompt Principles:**
- Break down into small, testable tasks
- Each task should touch ≤ 5 files
- Tasks have clear acceptance criteria
- Dependencies are explicit

#### 2. ImplementerAgent

**Input:**
```python
{
    "task": Task,
    "state": BuildState,
    "relevant_files": {
        "path/to/file": "file content snippet..."
    },
    "context": {
        "previous_attempts": [...],
        "reviewer_feedback": [...]
    }
}
```

**Output:** `PatchSet` (unified diff only)

**System Prompt Principles:**
- Produce unified diff format
- Keep patches small and focused
- Include "notes" explaining changes
- Don't touch files outside task scope

#### 3. ReviewerAgent

**Input:**
```python
{
    "task": Task,
    "patchset": PatchSet,
    "validation_report": ValidationReport,
    "check_report": CheckReport,
    "acceptance_criteria": [...]
}
```

**Output:** `ReviewReport`

**System Prompt Principles:**
- Block if validation fails
- Block if checks fail
- Request specific fixes, not vague feedback
- Approve only if all acceptance criteria met

### Tools Layer (backend/app/services/build_runtime/tools.py)

#### Repo Tools

```python
class RepoTools:
    """File system operations for the build."""

    async def read(self, path: str, start_line: int = 0, end_line: int = None) -> str:
        """Read file content (read-only for Planner/Reviewer)."""

    async def search(self, query: str) -> List[str]:
        """Search for files or patterns."""

    async def apply_patch(self, diff: str) -> Dict[str, List[int]]:
        """
        Apply unified diff to files.
        Returns: {"touched": [...], "errors": [...], "applied": bool}
        """
```

#### Validate Tools

```python
class ValidateTools:
    """Run the existing validator pipeline."""

    async def run(self, html: str, js: str = None) -> ValidationReport:
        """Run full validator pipeline (sanitize, AST check, runtime check)."""
```

#### Check Tools

```python
class CheckTools:
    """Run typecheck, lint, and unit tests."""

    async def typecheck(self) -> Dict:
        """Run frontend typecheck (pnpm typecheck)."""

    async def lint(self) -> Dict:
        """Run frontend lint (pnpm lint)."""

    async def unit(self) -> Dict:
        """Run backend unit tests (pytest)."""

    async def all(self) -> CheckReport:
        """Run all checks and return combined report."""
```

#### Snapshot Tools

```python
class SnapshotTools:
    """Manage build snapshots."""

    async def create(self, reason: str, metadata: Dict = None) -> str:
        """Create snapshot after patch application."""

    async def restore(self, snapshot_id: str) -> bool:
        """Revert to previous snapshot."""
```

### Orchestrator (backend/app/services/build_runtime/orchestrator.py)

```python
class BuildOrchestrator:
    """Deterministic state machine for the build loop."""

    async def start(
        self,
        project_id: str,
        user_id: str,
        brief: Dict,
        build_plan: Dict,
        product_doc: Dict
    ) -> BuildState:
        """Create a new build run."""
        # Create BuildState, persist, return
        pass

    async def step(
        self,
        build_id: str,
        user_message: str = None,
        mode: str = "auto"
    ) -> BuildState:
        """
        Advance the build by one step.

        Mode options:
        - "auto": Run full loop (plan → implement → verify → review)
        - "plan_only": Only call PlannerAgent
        - "implement_only": Only call ImplementerAgent (for fixes)
        - "verify_only": Only run verification
        """
        # Load state
        state = await self.storage.get(build_id)

        # Handle terminal states
        if state.is_terminal:
            return state

        # State machine transitions
        if state.phase == "planning":
            return await self._plan_step(state)
        elif state.phase == "implementing":
            return await self._implement_step(state, user_message)
        elif state.phase == "verifying":
            return await self._verify_step(state)
        elif state.phase == "reviewing":
            return await self._review_step(state)
        elif state.phase == "iterating":
            return await self._iterate_step(state, user_message)

        return state

    async def abort(self, build_id: str) -> BuildState:
        """Stop the build."""
        pass

    # === Private Step Methods ===

    async def _plan_step(self, state: BuildState) -> BuildState:
        """Call PlannerAgent to create BuildGraph."""
        if not state.build_graph:
            graph = await self.planner.run(
                brief=state.brief,
                build_plan=state.build_plan,
                product_doc=state.product_doc
            )
            state.build_graph = graph

        # Pick next todo task
        next_task = self._pick_next_task(state)
        if next_task:
            state.current_task_id = next_task.id
            next_task.status = "doing"

        state.phase = "implementing"
        return await self._save(state)

    async def _implement_step(self, state: BuildState, user_message: str = None) -> BuildState:
        """Call ImplementerAgent to create patch."""
        task = state.get_current_task()
        if not task:
            state.phase = "ready"
            return await self._save(state)

        # Get relevant files for context
        relevant_files = await self.repo_tools.get_files_for_task(task)

        # Build context
        context = {"reviewer_feedback": user_message} if user_message else {}

        # Generate patch
        patch = await self.implementer.run(
            task=task,
            state=state,
            relevant_files=relevant_files,
            context=context
        )

        # Apply patch
        result = await self.repo_tools.apply_patch(patch.diff)

        if result["applied"]:
            state.last_patch = patch
            state.patch_sets.append(patch)
            state.phase = "verifying"
        else:
            # Patch failed - log error and stay in implementing
            state.history.append(BuildHistoryEvent(
                phase="implementing",
                action="patch_failed",
                details={"error": result.get("error")}
            ))

        return await self._save(state)

    async def _verify_step(self, state: BuildState) -> BuildState:
        """Run validation and checks."""
        # Get current HTML from draft
        html = await self.draft_service.get_html(state.project_id)

        # Run validator
        validation = await self.validate_tools.run(html)
        state.last_validation = validation
        state.validation_reports.append(validation)

        # Run checks
        checks = await self.check_tools.all()
        state.last_checks = checks
        state.check_reports.append(checks)

        state.phase = "reviewing"
        return await self._save(state)

    async def _review_step(self, state: BuildState) -> BuildState:
        """Call ReviewerAgent."""
        task = state.get_current_task()
        if not task:
            state.phase = "ready"
            return await self._save(state)

        review = await self.reviewer.run(
            task=task,
            patchset=state.last_patch,
            validation_report=state.last_validation,
            check_report=state.last_checks,
            acceptance_criteria=task.acceptance
        )

        state.last_review = review
        state.review_reports.append(review)

        if review.decision == "approve":
            # Mark task done
            task.status = "done"
            task.completed_at = datetime.utcnow()

            if state.all_tasks_done:
                state.phase = "ready"
                state.completed_at = datetime.utcnow()
            else:
                state.phase = "implementing"
                state.current_task_id = None
        else:
            # Request changes - go to iterating
            state.phase = "iterating"

        state.history.append(BuildHistoryEvent(
            phase="reviewing",
            action=review.decision,
            details={"reasons": review.reasons}
        ))

        return await self._save(state)

    async def _iterate_step(self, state: BuildState, user_message: str = None) -> BuildState:
        """Implement fixes from reviewer feedback."""
        # Return to implementing with context
        state.phase = "implementing"
        return await self._implement_step(state, user_message)

    # === Helper Methods ===

    def _pick_next_task(self, state: BuildState) -> Optional[Task]:
        """Pick next task with no unmet dependencies."""
        if not state.build_graph:
            return None

        done_ids = {t.id for t in state.build_graph.tasks if t.status == "done"}

        for task in state.build_graph.tasks:
            if task.status == "todo":
                deps_done = all(d in done_ids for d in task.depends_on)
                if deps_done:
                    return task

        return None

    async def _save(self, state: BuildState) -> BuildState:
        """Persist state and return."""
        state.updated_at = datetime.utcnow()
        await self.storage.save(state)
        return state
```

### Persistence (backend/app/services/build_runtime/storage.py)

```python
class BuildStorage:
    """DB persistence for build artifacts."""

    async def create(self, state: BuildState) -> BuildState:
        """Create new build run."""
        pass

    async def get(self, build_id: str) -> Optional[BuildState]:
        """Get build by ID."""
        pass

    async def save(self, state: BuildState) -> None:
        """Update existing build."""
        pass

    async def list_by_project(self, project_id: str) -> List[BuildState]:
        """List all builds for a project."""
        pass

    async def get_latest_by_project(self, project_id: str) -> Optional[BuildState]:
        """Get most recent build for a project."""
        pass
```

### API Endpoints (backend/app/api/build.py)

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/build", tags=["build"])

class StartBuildRequest(BaseModel):
    project_id: str
    seed: dict  # {brief, build_plan, product_doc}

class StepRequest(BaseModel):
    build_id: str
    user_message: str = None
    mode: str = "auto"  # "auto" | "plan_only" | "implement_only" | "verify_only"


@router.post("/start")
async def start_build(
    req: StartBuildRequest,
    user_id: str = Depends(get_current_user)
) -> BuildState:
    """Start a new build run from interview artifacts."""
    return await orchestrator.start(
        project_id=req.project_id,
        user_id=user_id,
        brief=req.seed.get("brief", {}),
        build_plan=req.seed.get("build_plan", {}),
        product_doc=req.seed.get("product_doc", {})
    )


@router.post("/step")
async def step_build(
    req: StepRequest,
    user_id: str = Depends(get_current_user)
) -> BuildState:
    """Advance build by one step."""
    state = await orchestrator.step(
        build_id=req.build_id,
        user_message=req.user_message,
        mode=req.mode
    )

    if not state:
        raise HTTPException(404, "Build not found")

    return state


@router.get("/{build_id}")
async def get_build(
    build_id: str,
    user_id: str = Depends(get_current_user)
) -> BuildState:
    """Get current build state."""
    state = await storage.get(build_id)
    if not state:
        raise HTTPException(404, "Build not found")
    return state


@router.post("/{build_id}/abort")
async def abort_build(
    build_id: str,
    user_id: str = Depends(get_current_user)
) -> BuildState:
    """Abort a running build."""
    return await orchestrator.abort(build_id)


@router.get("/{build_id}/can-publish")
async def can_publish(
    build_id: str,
    user_id: str = Depends(get_current_user)
) -> dict:
    """Check if build is ready for publish."""
    state = await storage.get(build_id)
    if not state:
        raise HTTPException(404, "Build not found")

    can_publish = (
        state.phase == "ready" and
        state.last_validation is not None and
        state.last_validation.ok and
        state.last_checks is not None and
        state.last_checks.ok
    )

    return {
        "can_publish": can_publish,
        "reasons": [] if can_publish else [
            "Build not in ready state" if state.phase != "ready" else None,
            "Validation failed" if state.last_validation and not state.last_validation.ok else None,
            "Checks failed" if state.last_checks and not state.last_checks.ok else None
        ]
    }
```

---

## Part C: Frontend Changes

### Build Timeline Panel (NEW)

A panel showing build progress with ability to step through the loop:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Build Timeline                                                            [−] │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Phase: Implementing                                     [Abort Build]          │
│                                                                                 │
│  ┌─ Task 1: Landing page hero section                                 [Done] │
│  │  ○ Contact form with validation                                    [Todo] │
│  │  ○ Feature cards grid                                              [Todo] │
│  │  ○ Footer with links                                               [Todo] │
│  │                                                                            │
│  ├─ Current: Task 2 - Contact form with validation                        [Doing]│
│  │                                                                            │
│  │  Acceptance Criteria:                                                 │
│  │  ✓ Form has name, email, message fields                              │
│  │  ✓ Email validation (simple regex)                                   │
│  │  ✓ Submit shows success toast                                        │
│  │  ✓ Form clears after submission                                      │
│  │                                                                            │
│  ├─ Last Patch                                                            │
│  │  Files touched: 3                                                     │
│  │  - frontend/src/components/ContactForm.tsx                           │
│  │  - frontend/src/components/FormFields.tsx                            │
│  │  - frontend/src/runtime/forms.ts                                      │
│  │                                                                            │
│  │  Notes: Added form validation, toast notification, submit handler     │
│  │                                                                            │
│  ├─ Verification                                                          │
│  │  ✓ Validator: Passed (0 errors)                                       │
│  │  ⏳ Typecheck: Running...                                             │
│  │  ⏳ Lint: Running...                                                  │
│  │  ⏳ Unit: Running...                                                  │
│  │                                                                            │
│  └─ Review                                                                 │
│     Waiting for reviewer...                                               │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  [Run Next Step]  [Retry Step]  [Revert Last Patch]                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Component Structure

```
src/
├── components/
│   ├── build/                      # NEW: Build runtime components
│   │   ├── BuildTimeline.tsx       # Main timeline panel
│   │   ├── TaskList.tsx            # Task list with status
│   │   ├── TaskItem.tsx            # Single task display
│   │   ├── CurrentTaskCard.tsx     # Active task details
│   │   ├── PatchSummary.tsx        # Last patch info
│   │   ├── VerificationStatus.tsx  # Validation + checks status
│   │   ├── ReviewStatus.tsx        # Reviewer decision
│   │   └── BuildControls.tsx       # Step, abort, revert buttons
│   │
│   └── ...
│
├── stores/
│   ├── buildStore.ts               # NEW: Build state management
│   └── ...
```

### Build Store (frontend/src/stores/buildStore.ts)

```typescript
import { create } from 'zustand';

interface BuildState {
  // State
  buildId: string | null;
  phase: string | null;
  currentTaskId: string | null;
  buildGraph: BuildGraph | null;
  lastPatch: PatchSet | null;
  lastValidation: ValidationReport | null;
  lastChecks: CheckReport | null;
  lastReview: ReviewReport | null;
  history: BuildHistoryEvent[];

  // Actions
  startBuild: (projectId: string, seed: BuildSeed) => Promise<void>;
  stepBuild: (userMessage?: string) => Promise<void>;
  abortBuild: () => Promise<void>;
  revertPatch: () => Promise<void>;
  checkPublishReady: () => Promise<boolean>;

  // State updates
  setBuild: (state: BuildState) => void;
}

export const useBuildStore = create<BuildState>((set, get) => ({
  buildId: null,
  phase: null,
  currentTaskId: null,
  buildGraph: null,
  lastPatch: null,
  lastValidation: null,
  lastChecks: null,
  lastReview: null,
  history: [],

  async startBuild(projectId, seed) {
    const response = await fetch('/api/build/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, seed })
    });
    const state = await response.json();
    set({ ...state, buildId: state.build_id });
  },

  async stepBuild(userMessage) {
    const { buildId } = get();
    if (!buildId) return;

    const response = await fetch('/api/build/step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ build_id: buildId, user_message: userMessage })
    });
    const state = await response.json();
    set({ ...state, buildId: state.build_id });
  },

  async abortBuild() {
    const { buildId } = get();
    if (!buildId) return;

    const response = await fetch(`/api/build/${buildId}/abort`, {
      method: 'POST'
    });
    const state = await response.json();
    set({ ...state, buildId: state.build_id });
  },

  async revertPatch() {
    // Use snapshot system to revert
    const { buildId } = get();
    // Implementation depends on snapshot service
  },

  async checkPublishReady() {
    const { buildId } = get();
    if (!buildId) return false;

    const response = await fetch(`/api/build/${buildId}/can-publish`);
    const result = await response.json();
    return result.can_publish;
  },

  setBuild(state) {
    set({ ...state, buildId: state.build_id });
  }
}));
```

---

## Part D: Publish Gating

Publishing endpoint must check build state:

```python
@router.post("/api/projects/{project_id}/publish")
async def publish_project(
    project_id: str,
    user_id: str = Depends(get_current_user)
):
    """Publish project - only allowed if build is ready."""

    # Check for active build
    latest_build = await storage.get_latest_by_project(project_id)

    if latest_build and latest_build.phase not in {"ready", "aborted", "error"}:
        raise HTTPException(
            409,
            detail={
                "code": "BUILD_IN_PROGRESS",
                "message": "A build is in progress. Please wait for it to complete.",
                "build_id": latest_build.build_id,
                "phase": latest_build.phase
            }
        )

    # If there was a build, check it passed verification
    if latest_build:
        if not latest_build.last_validation or not latest_build.last_validation.ok:
            raise HTTPException(
                409,
                detail={
                    "code": "VALIDATION_FAILED",
                    "message": "Last build failed validation. Please fix issues and retry."
                }
            )

        if not latest_build.last_checks or not latest_build.last_checks.ok:
            raise HTTPException(
                409,
                detail={
                    "code": "CHECKS_FAILED",
                    "message": "Last build failed checks. Please fix issues and retry."
                }
            )

        if latest_build.phase != "ready":
            raise HTTPException(
                409,
                detail={
                    "code": "BUILD_NOT_READY",
                    "message": "Build is not in ready state."
                }
            )

    # Proceed with publish...
```

---

## Part E: Settings Page

### Route: `/settings`

Centralized settings - language, model, design defaults, notifications:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Settings                                                            [Save]   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  🌐 Language / 语言                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  ◉ English                                                              │   │
│  │  ○ 中文                                                                 │   │
│  │  ○ 日本語 (Japanese)                                                    │   │
│  │  ☑ Auto-detect from my messages                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  🤖 AI Model                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  Preferred Model:                                                       │   │
│  │  ◉ GLM-4.7 (智谱 AI) - Fast, good for Chinese                         │   │
│  │  ○ DeepSeek V3 - Powerful, great for complex tasks                     │   │
│  │  ○ Qwen (通义千问) - Balanced performance                              │   │
│  │  ○ Doubao (豆包) - Fast and affordable                                │   │
│  │  ○ Kimi K2 (月之暗面) - Excellent for long context                     │   │
│  │                                                                         │   │
│  │  Region: ◉ Auto  ○ China  ○ US                                       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  🎨 Default Design System                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  New projects start with:                                              │   │
│  │  • Primary Color: [#2563eb]  [Change]                                  │   │
│  │  • Font: Inter  [Change]                                               │   │
│  │  • Spacing: Comfortable  [Change]                                      │   │
│  │  • Border Radius: Medium  [Change]                                      │   │
│  │                                                                         │   │
│  │  Preset Themes:                                                          │   │
│  │  [Minimal] [Modern] [Playful] [Elegant] [Dark]                          │   │
│  │                                                                         │   │
│  │  [Edit Default Design →]                                                │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  📧 Email Notifications                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  ☑ Send me emails for:                                                 │   │
│  │    ☑ Form submissions on my pages                                     │   │
│  │    ☐ Weekly analytics summary                                         │   │
│  │    ☐ Project updates and tips                                         │   │
│  │                                                                         │   │
│  │  Notification Email:                                                   │   │
│  │  user@example.com  [Change]                                            │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  🔔 Browser Notifications                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  Browser notifications: ☑ Enabled                                      │   │
│  │                                                                         │   │
│  │  Notify me about:                                                       │   │
│  │    ☑ New form submissions                                              │   │
│  │    ☑ Project published                                                │   │
│  │    ☐ Generation complete                                               │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  💾 Account & Data                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  Storage: 2.4 MB used of 1 GB                                          │   │
│  │  Projects: 2 of 3 (Free plan)                                          │   │
│  │                                                                         │   │
│  │  [Export All Data]  [View Plans]  [Delete Account]                      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part F: Frontend Redesign

### New Component Structure

```
src/
├── components/
│   ├── ui/                        # Shared UI primitives
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Modal.tsx
│   │   ├── Tabs.tsx
│   │   ├── Badge.tsx
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── Switch.tsx
│   │   ├── IconButton.tsx
│   │   ├── DropdownMenu.tsx
│   │   └── index.ts
│   │
│   ├── layout/                    # Layout wrappers
│   │   ├── PageLayout.tsx         # Header + content wrapper
│   │   ├── EditorLayout.tsx       # Editor shell
│   │   └── DashboardLayout.tsx    # Dashboard with sidebar
│   │
│   ├── editor/                    # Editor components
│   │   ├── EditorContainer.tsx    # Main editor (simplified from EditorPage)
│   │   ├── ChatPanel.tsx          # Chat + interview (cleaner header)
│   │   ├── ChatInput.tsx          # Input area
│   │   ├── MessageList.tsx        # Messages + interview cards
│   │   ├── PreviewPane.tsx        # Preview wrapper
│   │   ├── EditorToolbar.tsx      # Header (grouped actions)
│   │   ├── QuickActions.tsx       # Quick action chips
│   │   └── BuildTimeline.tsx      # NEW: Agentic build timeline
│   │
│   ├── interview/                 # Interview components (KEPT)
│   │   ├── InterviewGroup.tsx
│   │   ├── QuestionOption.tsx
│   │   ├── AgentCallout.tsx
│   │   ├── BuildPlanCard.tsx
│   │   └── ProductDocumentCard.tsx
│   │
│   ├── settings/                  # Settings components
│   │   ├── SettingsPage.tsx
│   │   ├── LanguageSection.tsx
│   │   ├── ModelSection.tsx
│   │   ├── DesignSection.tsx
│   │   ├── NotificationSection.tsx
│   │   └── AccountSection.tsx
│   │
│   ├── dashboard/                 # Dashboard
│   │   ├── DashboardPage.tsx
│   │   ├── ProjectCard.tsx
│   │   ├── StatsOverview.tsx
│   │   └── RecentActivity.tsx
│   │
│   ├── build/                     # NEW: Build runtime
│   │   ├── BuildTimeline.tsx
│   │   ├── TaskList.tsx
│   │   ├── TaskItem.tsx
│   │   ├── CurrentTaskCard.tsx
│   │   ├── PatchSummary.tsx
│   │   ├── VerificationStatus.tsx
│   │   └── BuildControls.tsx
│   │
│   └── ... (keep existing)
│
├── pages/
│   ├── HomePage.tsx               # Landing page
│   ├── NewPage.tsx                # /new - empty editor
│   ├── EditorPage.tsx             # Simplified wrapper
│   ├── DashboardPage.tsx          # /project/:id
│   ├── SettingsPage.tsx           # /settings
│   └── ... (keep existing)
│
└── stores/
    ├── settingsStore.ts           # Settings state
    └── buildStore.ts              # NEW: Build state
```

### New Routes

```
/                           → HomePage (landing)
/new                        → NewPage (empty editor, auto-creates project)
/settings                   → SettingsPage (NEW)
/project/:projectId         → DashboardPage (project hub)
/project/:projectId/editor  → EditorPage
/project/:projectId/analytics → AnalyticsPage
/project/:projectId/submissions → SubmissionsPage
/project/:projectId/experiments → ExperimentsPage
/project/:projectId/assets  → AssetsPage
/p/:publicId                → PublishedPage
```

---

## Implementation Roadmap

### Phase 1: Build Runtime Foundation (Week 1-2)

1. **Create build_runtime module**
   - `backend/app/services/build_runtime/__init__.py`
   - `backend/app/services/build_runtime/models.py`
   - `backend/app/services/build_runtime/storage.py`

2. **Add DB table for build_runs**
   - `build_id`, `project_id`, `state_json`, timestamps
   - Migration script

3. **Implement API endpoints**
   - `POST /api/build/start`
   - `POST /api/build/step`
   - `GET /api/build/{build_id}`
   - `POST /api/build/{build_id}/abort`
   - `GET /api/build/{build_id}/can-publish`

### Phase 2: Tool Layer (Week 2)

1. **Implement repo tools**
   - `repo.read()`
   - `repo.search()`
   - `repo.apply_patch()`

2. **Integrate existing validator**
   - Wrap `validate.run()` for use in orchestrator

3. **Implement check tools**
   - `check.typecheck()` → `pnpm -C frontend typecheck`
   - `check.lint()` → `pnpm -C frontend lint`
   - `check.unit()` → `pytest -q`

### Phase 3: Agents (Week 3)

1. **PlannerAgent**
   - System prompt for task breakdown
   - Output parsing for `BuildGraph`

2. **ImplementerAgent**
   - System prompt for patch generation
   - Output parsing for `PatchSet`

3. **ReviewerAgent**
   - System prompt for review logic
   - Decision criteria: validation, checks, acceptance

### Phase 4: Orchestrator (Week 3-4)

1. **State machine implementation**
   - `planning → implementing → verifying → reviewing → iterating → ready`

2. **Step logic for each phase**
   - Handle transitions
   - Error handling
   - History logging

3. **Publish gating**
   - Check build state before publish
   - Return 409 with reasons if blocked

### Phase 5: Frontend Timeline UI (Week 4-5)

1. **Create build store**
   - `frontend/src/stores/buildStore.ts`

2. **Build Timeline panel**
   - Task list with status
   - Current task details
   - Patch summary
   - Verification status
   - Review status
   - Controls (step, abort, revert)

3. **Integrate with EditorPage**
   - Show timeline panel during build
   - Auto-refresh on step completion

### Phase 6: Settings Page (Week 5)

1. **Create settings page components**
2. **Implement settings API**
3. **Create settingsStore**
4. **Move language/model selectors from ChatPanel**

### Phase 7: Intent Detection (Week 6)

1. **Create intent detection service**
2. **Update interview orchestrator**
3. **Test intent detection accuracy**

---

## Success Metrics (v3)

| Metric | v2 | v3 Target |
|--------|----|-----------|
| Time to first message | 30-60 sec | < 10 sec |
| Template drop-off | ~20% | 0% |
| Interview completion | > 80% | > 80% |
| First-gen acceptance | > 70% | > 75% (iterative improves) |
| Settings page usage | N/A | > 30% |
| Build loop completion | N/A | > 60% |
| Publish on first attempt | N/A | > 50% |
| Iteration success rate | N/A | > 70% |

---

## v2 → v3 Bridge (Backward Compatibility)

The v3 build loop is additive and doesn't break v2 workflows:

1. **Interview v2 still works**
   - Brief, BuildPlan, ProductDocument still produced
   - These become inputs to build loop

2. **Snapshot system preserved**
   - Build loop creates snapshots after patches
   - Existing snapshot functionality unchanged

3. **Publish still works**
   - Direct publish allowed (no build)
   - Publish with build requires `ready` state

4. **Gradual migration path**
   - v3 features can be enabled progressively
   - Old users can continue v2 flow

---

## Summary

v3 transforms Zaoya from a single-pass generator into an agentic builder:

| What's Removed | What's Kept | What's Added |
|----------------|-------------|--------------|
| Template selection page | Adaptive interview | Intent detection |
| Template grid UI | Question groups | Build Orchestrator |
| Template form inputs | Agent callouts | Planner/Implementer/Reviewer agents |
| Template categories | Build plan preview | PatchSet + diff-based iteration |
| Single-pass generation | Product document | BuildTimeline UI |
| | Quick actions | Verification pipeline |
| | Snapshot system | Publish gating |

**Result**: Zero-friction start, iterative development, Lovable/Bolt-style build experience.

---

## Appendix: Key Interface Contracts

### BuildSeed (input to start)

```json
{
  "project_id": "proj_abc123",
  "seed": {
    "brief": {
      "title": "Wedding RSVP",
      "description": "...",
      "intent": "event-invitation",
      "collected_data": {...}
    },
    "build_plan": {
      "pages": [...],
      "features": [...],
      "design_tokens": {...}
    },
    "product_doc": {
      "screens": [...],
      "data_flows": [...],
      "requirements": [...]
    }
  }
}
```

### PatchSet format

```json
{
  "id": "ps_xyz789",
  "task_id": "task_002",
  "diff": "--- a/frontend/src/components/ContactForm.tsx\n+++ b/frontend/src/components/ContactForm.tsx\n@@ -10,6 +10,8 @@\n+import { validateEmail } from '@/utils/validation';\n+\n export function ContactForm() {\   const [email, setEmail] = useState('');\n \n@@ -25,6 +27,10 @@\n     if (!validateEmail(email)) {\       setError('Please enter a valid email');\n       return false;\n     }\n+    await Zaoya.submitForm({ email, message });\n+    Zaoya.toast('Message sent!');\n+    setEmail('');\n+    setMessage('');\n     return true;\n   }",
  "touched_files": [
    "frontend/src/components/ContactForm.tsx",
    "frontend/src/utils/validation.ts"
  ],
  "notes": "Added email validation, form submission, and success toast. Clears form after submit."
}
```

---

**Document Version**: 3.1
**Last Updated**: 2026-01-25
**Status**: Draft - Ready for Implementation
**Change Log**:
- Added Part B: Build Orchestrator (agents, tools, state machine)
- Added Part C: Frontend Build Timeline Panel
- Added Part D: Publish Gating
- Updated Part E: Settings Page
- Updated Part F: Frontend Redesign with new build components
