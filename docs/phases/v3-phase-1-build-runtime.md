# Phase 1: Build Runtime Foundation

**Duration**: Week 1-2
**Status**: Pending

---

## Phase Overview

This phase establishes the foundational infrastructure for the agentic build loop. It creates the `build_runtime` module with all core Pydantic models, persistence layer, and API endpoints. This is the scaffolding upon which all subsequent phases depend.

The build runtime is the "source of truth" for any build run - it tracks the complete state machine, all artifacts (tasks, patches, reports), and history. Without this foundation, no other phase can proceed.

---

## Prerequisites

### Must Be Completed Before Starting
1. **Interview v2 artifacts defined** - `ProjectBrief`, `BuildPlan`, `ProductDocument` schemas must exist in `backend/app/models/schemas/`
2. **Database infrastructure** - SQLAlchemy setup and existing project/snapshot tables
3. **FastAPI application structure** - Router pattern in `backend/app/api/`

### External Dependencies
- None (self-contained backend work)

### Knowledge Requirements
- Understanding of existing Pydantic model patterns in the codebase
- Familiarity with SQLAlchemy async patterns
- FastAPI dependency injection patterns

---

## Detailed Tasks

### Task 1.1: Create Module Structure

**Description**: Create the `build_runtime` directory and `__init__.py`

**Steps**:
1. Create `backend/app/services/build_runtime/`
2. Create `__init__.py` with module exports
3. Create empty placeholder files for: `models.py`, `storage.py`, `tools.py`, `agents.py`, `orchestrator.py`, `policies.py`

**File: `backend/app/services/build_runtime/__init__.py`**
```python
"""Build Runtime - Agentic build orchestration for Zaoya."""

from .models import (
    BuildState,
    BuildGraph,
    Task,
    PatchSet,
    ValidationReport,
    CheckReport,
    ReviewReport,
    BuildPhase,
    TaskStatus,
    ReviewDecision,
)
from .orchestrator import BuildOrchestrator
from .storage import BuildStorage

__all__ = [
    "BuildState",
    "BuildGraph",
    "Task",
    "PatchSet",
    "ValidationReport",
    "CheckReport",
    "ReviewReport",
    "BuildPhase",
    "TaskStatus",
    "ReviewDecision",
    "BuildOrchestrator",
    "BuildStorage",
]
```

**Dependencies**: None
**Parallelizable**: Yes (with other task 1.x tasks)

---

### Task 1.2: Implement Pydantic Models

**Description**: Create all data models in `models.py` per SPEC-v3 specification

**Steps**:
1. Define enums (`BuildPhase`, `TaskStatus`, `ReviewDecision`)
2. Implement `Task` model
3. Implement `BuildGraph` model
4. Implement `PatchSet` model
5. Implement `ValidationReport` model
6. Implement `CheckReport` model
7. Implement `ReviewReport` model
8. Implement `BuildHistoryEvent` model
9. Implement `BuildState` model with properties

**File: `backend/app/services/build_runtime/models.py`**

Key code structure:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
from enum import Enum

# === Enums ===

class BuildPhase(str, Enum):
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    VERIFYING = "verifying"
    REVIEWING = "reviewing"
    ITERATING = "iterating"
    READY = "ready"
    ABORTED = "aborted"
    ERROR = "error"

class TaskStatus(str, Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"
    BLOCKED = "blocked"

class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"

# === Core Artifacts ===

class Task(BaseModel):
    """Single implementable unit of work."""
    id: str
    title: str
    goal: str
    acceptance: List[str]
    depends_on: List[str] = []
    files_expected: List[str] = []
    status: TaskStatus = TaskStatus.TODO
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "task_001",
                    "title": "Contact form validation",
                    "goal": "Add email and message validation to contact form",
                    "acceptance": [
                        "Email field validates format",
                        "Message field has min length",
                        "Submit disabled until valid"
                    ],
                    "depends_on": [],
                    "files_expected": ["frontend/src/components/ContactForm.tsx"],
                    "status": "todo"
                }
            ]
        }
    }

class BuildGraph(BaseModel):
    """Plan of all tasks with dependencies."""
    tasks: List[Task]
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PatchSet(BaseModel):
    """Unified diff with metadata."""
    id: str
    task_id: str
    diff: str
    touched_files: List[str]
    notes: str = ""
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
    reasons: List[str] = []
    required_fixes: List[str] = []
    blocked_by: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BuildHistoryEvent(BaseModel):
    """Single event in build history."""
    ts: datetime = Field(default_factory=datetime.utcnow)
    phase: BuildPhase
    action: str
    details: Dict = Field(default_factory=dict)

class BuildState(BaseModel):
    """Complete build run state - the source of truth."""
    build_id: str
    project_id: str
    user_id: str
    phase: BuildPhase = BuildPhase.PLANNING
    current_task_id: Optional[str] = None

    # Inputs (from Interview v2)
    brief: Dict = Field(default_factory=dict)
    build_plan: Dict = Field(default_factory=dict)
    product_doc: Dict = Field(default_factory=dict)

    # Artifacts
    build_graph: Optional[BuildGraph] = None
    patch_sets: List[PatchSet] = []
    last_patch: Optional[PatchSet] = None

    validation_reports: List[ValidationReport] = []
    last_validation: Optional[ValidationReport] = None

    check_reports: List[CheckReport] = []
    last_checks: Optional[CheckReport] = None

    review_reports: List[ReviewReport] = []
    last_review: Optional[ReviewReport] = None

    # History
    history: List[BuildHistoryEvent] = []

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    @property
    def is_terminal(self) -> bool:
        """Check if build is in a terminal state."""
        return self.phase in {BuildPhase.READY, BuildPhase.ABORTED, BuildPhase.ERROR}

    @property
    def all_tasks_done(self) -> bool:
        """Check if all tasks are complete."""
        if not self.build_graph:
            return False
        return all(t.status == TaskStatus.DONE for t in self.build_graph.tasks)

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
        done_ids = {t.id for t in self.build_graph.tasks if t.status == TaskStatus.DONE}
        blocked = []
        for task in self.build_graph.tasks:
            if task.status == TaskStatus.TODO:
                deps_not_done = [d for d in task.depends_on if d not in done_ids]
                if deps_not_done:
                    blocked.append(task)
        return blocked

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        }
    }
```

**Dependencies**: Task 1.1
**Parallelizable**: No (sequential within task)

---

### Task 1.3: Create Database Migration

**Description**: Add `build_runs` table to store build state

**Steps**:
1. Create Alembic migration file for `build_runs` table
2. Define table schema with all necessary columns
3. Add indexes for efficient queries
4. Write downgrade migration

**File: `backend/alembic/versions/xxxx_create_build_runs_table.py`**

```python
"""create_build_runs_table

Revision ID: xxxx
Revises: xxxx
Create Date: 2026-01-25

"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic
revision: str = 'xxxx'
down_revision: Union[str, None] = None
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # Create build_runs table
    op.create_table(
        'build_runs',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('build_id', sa.String(50), nullable=False, index=True),
        sa.Column('project_id', sa.String(50), nullable=False, index=True),
        sa.Column('user_id', sa.String(50), nullable=False, index=True),
        sa.Column('phase', sa.String(20), nullable=False, default='planning'),
        sa.Column('current_task_id', sa.String(50), nullable=True),

        # JSON columns for complex data
        sa.Column('brief', sqlite.JSON, nullable=True),
        sa.Column('build_plan', sqlite.JSON, nullable=True),
        sa.Column('product_doc', sqlite.JSON, nullable=True),
        sa.Column('build_graph', sqlite.JSON, nullable=True),
        sa.Column('patch_sets', sqlite.JSON, nullable=True),
        sa.Column('last_patch', sqlite.JSON, nullable=True),
        sa.Column('validation_reports', sqlite.JSON, nullable=True),
        sa.Column('last_validation', sqlite.JSON, nullable=True),
        sa.Column('check_reports', sqlite.JSON, nullable=True),
        sa.Column('last_checks', sqlite.JSON, nullable=True),
        sa.Column('review_reports', sqlite.JSON, nullable=True),
        sa.Column('last_review', sqlite.JSON, nullable=True),
        sa.Column('history', sqlite.JSON, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=True),

        # Foreign keys (adjust based on existing tables)
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )

    # Create indexes for common query patterns
    op.create_index('ix_build_runs_project_phase', 'build_runs', ['project_id', 'phase'])
    op.create_index('ix_build_runs_created_at', 'build_runs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_build_runs_created_at', table_name='build_runs')
    op.drop_index('ix_build_runs_project_phase', table_name='build_runs')
    op.drop_table('build_runs')
```

**Dependencies**: Task 1.2
**Parallelizable**: No

---

### Task 1.4: Implement Storage Layer

**Description**: Create persistence helpers in `storage.py`

**File: `backend/app/services/build_runtime/storage.py`**

```python
"""Build storage for persistence of build artifacts."""

import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from .models import BuildState, BuildPhase


class BuildStorage:
    """DB persistence for build artifacts."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.table = "build_runs"  # Adjust based on actual table name

    async def create(self, state: BuildState) -> BuildState:
        """Create new build run."""
        state_dict = state.model_dump()
        state_dict["created_at"] = state_dict["created_at"].isoformat()
        state_dict["updated_at"] = state_dict["updated_at"].isoformat()

        # Convert complex objects to JSON
        for key in ["brief", "build_plan", "product_doc", "build_graph",
                    "patch_sets", "last_patch", "validation_reports",
                    "last_validation", "check_reports", "last_checks",
                    "review_reports", "last_review", "history"]:
            if state_dict.get(key) is not None:
                state_dict[key] = json.dumps(state_dict[key])

        query = f"""
            INSERT INTO {self.table}
            (build_id, project_id, user_id, phase, current_task_id,
             brief, build_plan, product_doc, build_graph, patch_sets,
             last_patch, validation_reports, last_validation, check_reports,
             last_checks, review_reports, last_review, history,
             created_at, updated_at)
            VALUES
            (:build_id, :project_id, :user_id, :phase, :current_task_id,
             :brief, :build_plan, :product_doc, :build_graph, :patch_sets,
             :last_patch, :validation_reports, :last_validation, :check_reports,
             :last_checks, :review_reports, :last_review, :history,
             :created_at, :updated_at)
        """
        await self.db.execute(query, state_dict)
        await self.db.commit()
        return state

    async def get(self, build_id: str) -> Optional[BuildState]:
        """Get build by ID."""
        query = f"SELECT * FROM {self.table} WHERE build_id = :build_id"
        result = await self.db.execute(query, {"build_id": build_id})
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_state(row)

    async def save(self, state: BuildState) -> None:
        """Update existing build."""
        state.updated_at = datetime.utcnow()
        state_dict = state.model_dump()
        state_dict["updated_at"] = state_dict["updated_at"].isoformat()

        for key in ["brief", "build_plan", "product_doc", "build_graph",
                    "patch_sets", "last_patch", "validation_reports",
                    "last_validation", "check_reports", "last_checks",
                    "review_reports", "last_review", "history"]:
            if state_dict.get(key) is not None:
                state_dict[key] = json.dumps(state_dict[key])

        query = f"""
            UPDATE {self.table} SET
            phase = :phase,
            current_task_id = :current_task_id,
            brief = :brief,
            build_plan = :build_plan,
            product_doc = :product_doc,
            build_graph = :build_graph,
            patch_sets = :patch_sets,
            last_patch = :last_patch,
            validation_reports = :validation_reports,
            last_validation = :last_validation,
            check_reports = :check_reports,
            last_checks = :last_checks,
            review_reports = :review_reports,
            last_review = :last_review,
            history = :history,
            updated_at = :updated_at,
            completed_at = :completed_at
            WHERE build_id = :build_id
        """
        await self.db.execute(query, state_dict)
        await self.db.commit()

    async def list_by_project(self, project_id: str) -> List[BuildState]:
        """List all builds for a project."""
        query = f"""
            SELECT * FROM {self.table}
            WHERE project_id = :project_id
            ORDER BY created_at DESC
        """
        result = await self.db.execute(query, {"project_id": project_id})
        return [self._row_to_state(row) for row in result.fetchall()]

    async def get_latest_by_project(self, project_id: str) -> Optional[BuildState]:
        """Get most recent build for a project."""
        query = f"""
            SELECT * FROM {self.table}
            WHERE project_id = :project_id
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = await self.db.execute(query, {"project_id": project_id})
        row = result.fetchone()

        if not row:
            return None
        return self._row_to_state(row)

    def _row_to_state(self, row) -> BuildState:
        """Convert database row to BuildState."""
        state_dict = dict(row._mapping)

        # Parse JSON columns
        for key in ["brief", "build_plan", "product_doc", "build_graph",
                    "patch_sets", "last_patch", "validation_reports",
                    "last_validation", "check_reports", "last_checks",
                    "review_reports", "last_review", "history"]:
            if state_dict.get(key) and isinstance(state_dict[key], str):
                try:
                    state_dict[key] = json.loads(state_dict[key])
                except json.JSONDecodeError:
                    state_dict[key] = None

        # Parse timestamps
        for key in ["created_at", "updated_at", "completed_at"]:
            if state_dict.get(key) and isinstance(state_dict[key], str):
                state_dict[key] = datetime.fromisoformat(state_dict[key])

        return BuildState(**state_dict)
```

**Dependencies**: Task 1.3
**Parallelizable**: No

---

### Task 1.5: Implement API Endpoints

**Description**: Create `backend/app/api/build.py` with all endpoints

**File: `backend/app/api/build.py`**

```python
"""Build API - Agentic build orchestration endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.models.db.user import User
from app.api.deps import get_current_user
from app.services.build_runtime.storage import BuildStorage
from app.services.build_runtime.models import BuildState

router = APIRouter(prefix="/api/build", tags=["build"])


class StartBuildRequest(BaseModel):
    project_id: str = Field(..., description="Project ID to build")
    seed: dict = Field(..., description="Build seed with brief, build_plan, product_doc")


class StepRequest(BaseModel):
    build_id: str = Field(..., description="Build ID to step")
    user_message: Optional[str] = Field(None, description="User feedback for iterating")
    mode: str = Field(
        default="auto",
        description="Step mode: auto | plan_only | implement_only | verify_only"
    )


class BuildResponse(BaseModel):
    build_id: str
    project_id: str
    phase: str
    current_task_id: Optional[str]
    build_graph: Optional[dict] = None
    last_patch: Optional[dict] = None
    last_validation: Optional[dict] = None
    last_checks: Optional[dict] = None
    last_review: Optional[dict] = None
    history: list


class CanPublishResponse(BaseModel):
    can_publish: bool
    reasons: list[str]


@router.post("/start", response_model=BuildResponse)
async def start_build(
    req: StartBuildRequest,
    user: User = Depends(get_current_user)
) -> BuildResponse:
    """
    Start a new build run from interview artifacts.

    Creates a new BuildState in 'planning' phase with the provided seed.
    """
    # Import here to avoid circular imports
    from app.services.build_runtime.orchestrator import orchestrator

    try:
        state = await orchestrator.start(
            project_id=req.project_id,
            user_id=user.id,
            brief=req.seed.get("brief", {}),
            build_plan=req.seed.get("build_plan", {}),
            product_doc=req.seed.get("product_doc", {})
        )
        return _state_to_response(state)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start build: {str(e)}"
        )


@router.post("/step", response_model=BuildResponse)
async def step_build(
    req: StepRequest,
    user: User = Depends(get_current_user)
) -> BuildResponse:
    """
    Advance build by one step.

    Depending on the current phase and mode, this will:
    - Planning: Create BuildGraph if needed, pick next task
    - Implementing: Generate patch for current task
    - Verifying: Run validation and checks
    - Reviewing: Get reviewer decision
    - Iterating: Apply fixes from review
    """
    from app.services.build_runtime.orchestrator import orchestrator

    try:
        state = await orchestrator.step(
            build_id=req.build_id,
            user_message=req.user_message,
            mode=req.mode
        )
        return _state_to_response(state)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to step build: {str(e)}"
        )


@router.get("/{build_id}", response_model=BuildResponse)
async def get_build(
    build_id: str,
    user: User = Depends(get_current_user)
) -> BuildResponse:
    """Get current build state."""
    storage = BuildStorage(db)  # Adjust based on DI pattern

    state = await storage.get(build_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Build {build_id} not found"
        )

    # Verify ownership
    if state.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this build"
        )

    return _state_to_response(state)


@router.post("/{build_id}/abort", response_model=BuildResponse)
async def abort_build(
    build_id: str,
    user: User = Depends(get_current_user)
) -> BuildResponse:
    """Abort a running build."""
    from app.services.build_runtime.orchestrator import orchestrator

    try:
        state = await orchestrator.abort(build_id)
        return _state_to_response(state)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{build_id}/can-publish", response_model=CanPublishResponse)
async def can_publish(
    build_id: str,
    user: User = Depends(get_current_user)
) -> CanPublishResponse:
    """Check if build is ready for publish."""
    storage = BuildStorage(db)

    state = await storage.get(build_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Build {build_id} not found"
        )

    can_publish = (
        state.phase.value == "ready" and
        state.last_validation is not None and
        state.last_validation.ok and
        state.last_checks is not None and
        state.last_checks.ok
    )

    reasons = []
    if state.phase.value != "ready":
        reasons.append(f"Build not in ready state (current: {state.phase.value})")
    if state.last_validation is None or not state.last_validation.ok:
        reasons.append("Validation failed or not run")
    if state.last_checks is None or not state.last_checks.ok:
        reasons.append("Checks failed or not run")

    return CanPublishResponse(
        can_publish=can_publish,
        reasons=reasons if not can_publish else []
    )


def _state_to_response(state: BuildState) -> BuildResponse:
    """Convert BuildState to API response."""
    return BuildResponse(
        build_id=state.build_id,
        project_id=state.project_id,
        phase=state.phase.value,
        current_task_id=state.current_task_id,
        build_graph=state.build_graph.model_dump() if state.build_graph else None,
        last_patch=state.last_patch.model_dump() if state.last_patch else None,
        last_validation=state.last_validation.model_dump() if state.last_validation else None,
        last_checks=state.last_checks.model_dump() if state.last_checks else None,
        last_review=state.last_review.model_dump() if state.last_review else None,
        history=[h.model_dump() for h in state.history]
    )
```

**Dependencies**: Tasks 1.2, 1.4
**Parallelizable**: No

---

### Task 1.6: Wire API to Main Application

**Description**: Register the build router in `main.py`

**Steps**:
1. Import the build router in `backend/app/main.py`
2. Include it in the FastAPI app

**File: `backend/app/main.py` (additions)**

```python
from app.api.build import router as build_router

# Add to app.include_router() calls
app.include_router(build_router, prefix="")
```

**Dependencies**: Task 1.5
**Parallelizable**: No

---

## Technical Considerations

### Key Dependencies
- **SQLAlchemy 2.0** - Async database operations
- **Pydantic 2.x** - Data validation and serialization
- **Alembic** - Database migrations

### Architecture Decisions
1. **JSON storage for complex objects** - Store BuildGraph, PatchSets, etc. as JSON in SQLite for flexibility
2. **Enums as string enums** - Use `str, Enum` pattern for database compatibility
3. **Async storage** - Non-blocking DB operations for SSE compatibility

### JSON Serialization Challenges
- `datetime` fields need custom encoding
- Nested Pydantic models need proper serialization
- Consider using `model_dump(mode='json')` for Pydantic v2

### Database Considerations
- `build_id` should be UUID-based for uniqueness
- Indexes on `project_id` and `created_at` for common queries
- Consider soft-delete vs hard-delete strategy

---

## Acceptance Criteria

- [ ] `backend/app/services/build_runtime/` module exists with all files
- [ ] All Pydantic models serialize/deserialize correctly
- [ ] `build_runs` table created via Alembic migration
- [ ] `POST /api/build/start` creates a new build and returns BuildState
- [ ] `GET /api/build/{build_id}` retrieves build state
- [ ] `POST /api/build/step` advances build state
- [ ] `POST /api/build/{build_id}/abort` sets phase to "aborted"
- [ ] `GET /api/build/{build_id}/can-publish` returns correct status
- [ ] All endpoints return proper error codes (404, 409, 500)
- [ ] Build state persists correctly in database
- [ ] Tests cover storage and API endpoints

---

## Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| JSON serialization issues with nested models | Medium | Medium | Write serialization tests; use Pydantic's `mode='json'` |
| Circular imports between modules | Medium | Low | Use lazy imports in API; keep orchestrator minimal in models |
| Database schema changes require migration | Low | High | Version migrations carefully; test downgrade path |
| API response size grows too large | Medium | Low | Implement pagination for history; consider compression |

---

## Estimated Scope

**Complexity**: Large

**Key Effort Drivers**:
- Setting up proper async database operations
- Handling JSON serialization of complex nested objects
- Writing comprehensive tests for storage layer
- Error handling across all endpoints

**Estimated Lines of Code**: ~800-1200 (models + storage + API + tests)

---

## Testing Strategy

### Unit Tests
- Test Pydantic model serialization/deserialization
- Test BuildState properties (`is_terminal`, `all_tasks_done`, etc.)
- Test task dependency resolution logic

### Integration Tests
- Test API endpoints with mock storage
- Test database persistence with test database
- Test error cases (404, 403, 409)

### Test Files
- `backend/tests/unit/services/build_runtime/test_models.py`
- `backend/tests/unit/services/build_runtime/test_storage.py`
- `backend/tests/integration/api/test_build.py`
