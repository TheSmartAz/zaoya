"""Pydantic models for build runtime artifacts and state."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.models.schemas.interview import ProjectBrief, BuildPlan, ProductDocument


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
    depends_on: List[str] = Field(default_factory=list)
    files_expected: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.TODO
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "task_001",
                    "title": "Contact form validation",
                    "goal": "Add email and message validation to contact form",
                    "acceptance": [
                        "Email field validates format",
                        "Message field has min length",
                        "Submit disabled until valid",
                    ],
                    "depends_on": [],
                    "files_expected": ["frontend/src/components/ContactForm.tsx"],
                    "status": "todo",
                }
            ]
        }
    )

    @field_validator("files_expected")
    @classmethod
    def _limit_files_expected(cls, value: List[str]) -> List[str]:
        if len(value) > 5:
            raise ValueError("files_expected must contain at most 5 files")
        return value


class BuildGraph(BaseModel):
    """Plan of all tasks with dependencies."""

    tasks: List[Task]
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def _validate_tasks(self) -> "BuildGraph":
        task_count = len(self.tasks)
        if task_count > 15:
            raise ValueError("BuildGraph must contain at most 15 tasks")

        ids = [task.id for task in self.tasks]
        if len(set(ids)) != len(ids):
            raise ValueError("Task ids must be unique")

        id_set = set(ids)
        for task in self.tasks:
            for dep in task.depends_on:
                if dep == task.id:
                    raise ValueError("Task cannot depend on itself")
                if dep not in id_set:
                    raise ValueError(f"Task depends_on references unknown id: {dep}")

        return self


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AgentUsage(BaseModel):
    agent: str
    model: str
    usage: TokenUsage
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
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    error_details: List[dict] = Field(default_factory=list)
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
    reasons: List[str] = Field(default_factory=list)
    required_fixes: List[str] = Field(default_factory=list)
    blocked_by: List[str] = Field(default_factory=list)
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
    brief: ProjectBrief = Field(default_factory=ProjectBrief)
    build_plan: Optional[BuildPlan] = None
    product_doc: Optional[ProductDocument] = None

    # Artifacts
    build_graph: Optional[BuildGraph] = None
    patch_sets: List[PatchSet] = Field(default_factory=list)
    last_patch: Optional[PatchSet] = None

    validation_reports: List[ValidationReport] = Field(default_factory=list)
    last_validation: Optional[ValidationReport] = None

    check_reports: List[CheckReport] = Field(default_factory=list)
    last_checks: Optional[CheckReport] = None

    review_reports: List[ReviewReport] = Field(default_factory=list)
    last_review: Optional[ReviewReport] = None

    agent_usage: List["AgentUsage"] = Field(default_factory=list)
    last_agent_usage: Optional["AgentUsage"] = None

    # History
    history: List[BuildHistoryEvent] = Field(default_factory=list)

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
        blocked: List[Task] = []
        for task in self.build_graph.tasks:
            if task.status == TaskStatus.TODO:
                deps_not_done = [d for d in task.depends_on if d not in done_ids]
                if deps_not_done:
                    blocked.append(task)
        return blocked

    def total_token_usage(self) -> "TokenUsage":
        """Aggregate token usage across all agent calls."""
        prompt_total = 0
        completion_total = 0
        total_total = 0
        for entry in self.agent_usage:
            prompt_total += entry.usage.prompt_tokens
            completion_total += entry.usage.completion_tokens
            total_total += entry.usage.total_tokens
        if total_total == 0:
            total_total = prompt_total + completion_total
        return TokenUsage(
            prompt_tokens=prompt_total,
            completion_tokens=completion_total,
            total_tokens=total_total,
        )

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )
