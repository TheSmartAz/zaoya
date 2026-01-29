# Phase 4: Orchestrator

**Duration**: Week 3-4
**Status**: Implemented
**Depends On**: Phase 1 (Build Runtime Foundation), Phase 2 (Tool Layer), Phase 3 (Agents)

---

## Phase Overview

This phase implements the BuildOrchestrator - the state machine that coordinates the entire build loop. It advances the build through phases: `planning → implementing → verifying → reviewing → iterating → ready`.

The orchestrator is the "brain" that:
1. Decides what step to take based on current phase
2. Calls the appropriate agents
3. Runs tools (validation, checks)
4. Persists state after each step
5. Handles errors and history

**Current implementation notes**:
- Validation uses draft pages (via `DraftService`) when available.
- Validation and checks run concurrently.
- Agent usage is tracked per step and written into build history.

This is the core of the agentic build system.

---

## Prerequisites

### Must Be Completed Before Starting
1. **Phase 1 complete** - BuildState models and storage
2. **Phase 2 complete** - All tools (repo, validate, check, snapshot)
3. **Phase 3 complete** - All agents (planner, implementer, reviewer)

### Knowledge Requirements
- Understanding of state machine patterns
- Async/await patterns in Python
- Dependency injection in FastAPI

---

## Detailed Tasks

### Task 4.1: Create Orchestrator Class Structure

**Description**: Define the BuildOrchestrator class with phase transition logic

**File: `backend/app/services/build_runtime/orchestrator.py` (part 1)**

```python
"""Build Orchestrator - State machine for the agentic build loop."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from app.models.schemas.interview import BuildPlan, ProductDocument, ProjectBrief

from .agents import (
    ImplementerAgent,
    PlannerAgent,
    ReviewerAgent,
    create_implementer_agent,
    create_planner_agent,
    create_reviewer_agent,
)
from .models import (
    AgentUsage,
    BuildGraph,
    BuildHistoryEvent,
    BuildPhase,
    BuildState,
    CheckReport,
    PatchSet,
    ReviewDecision,
    ReviewReport,
    Task,
    TaskStatus,
    TokenUsage,
    ValidationReport,
)
from .storage import BuildStorage
from .tools import CheckTools, RepoTools, SnapshotTools, ValidateTools

logger = logging.getLogger(__name__)


class BuildOrchestrator:
    """Deterministic state machine for the build loop."""

    def __init__(
        self,
        storage: BuildStorage,
        planner: PlannerAgent | None = None,
        implementer: ImplementerAgent | None = None,
        reviewer: ReviewerAgent | None = None,
        repo_tools: RepoTools | None = None,
        validate_tools: ValidateTools | None = None,
        check_tools: CheckTools | None = None,
        snapshot_tools: SnapshotTools | None = None,
        project_path: str | None = None,
    ) -> None:
        self.storage = storage
        self.planner = planner or create_planner_agent()
        self.implementer = implementer or create_implementer_agent()
        self.reviewer = reviewer or create_reviewer_agent()

        project_path = project_path or "."
        self.repo_tools = repo_tools or RepoTools(project_path)
        self.validate_tools = validate_tools or ValidateTools()
        self.check_tools = check_tools or CheckTools(project_path)
        self.snapshot_tools = snapshot_tools

    async def start(
        self,
        project_id: str,
        user_id: str,
        brief: dict,
        build_plan: Optional[dict],
        product_doc: Optional[dict],
    ) -> BuildState:
        """Create a new BuildState and persist it."""
        build_id = str(uuid4())

        brief_model = ProjectBrief.model_validate(brief or {})
        build_plan_model = BuildPlan.model_validate(build_plan) if build_plan else None
        product_doc_model = ProductDocument.model_validate(product_doc) if product_doc else None

        state = BuildState(
            build_id=build_id,
            project_id=project_id,
            user_id=user_id,
            phase=BuildPhase.PLANNING,
            brief=brief_model,
            build_plan=build_plan_model,
            product_doc=product_doc_model,
        )
        state.history.append(
            BuildHistoryEvent(
                phase=BuildPhase.PLANNING,
                action="build_started",
                details={"project_id": project_id},
            )
        )

        await self.storage.create(state)
        logger.info("Started build %s for project %s", build_id, project_id)
        return state

    async def step(
        self,
        build_id: str,
        user_message: Optional[str] = None,
        mode: str = "auto",
    ) -> BuildState:
        """Advance build by one step."""
        state = await self.storage.get(build_id)
        if not state:
            raise ValueError(f"Build {build_id} not found")

        if state.is_terminal:
            logger.info("Build %s is terminal (%s)", build_id, state.phase)
            return state

        logger.info("Build %s stepping from %s", build_id, state.phase)

        if mode == "plan_only":
            state = await self._plan_step(state)
        elif mode == "implement_only":
            state = await self._implement_step(state, user_message)
        elif mode == "verify_only":
            state = await self._verify_step(state)
        else:
            state = await self._auto_step(state, user_message)

        return state

    async def abort(self, build_id: str) -> BuildState:
        """Abort a build run."""
        state = await self.storage.get(build_id)
        if not state:
            raise ValueError(f"Build {build_id} not found")

        state.phase = BuildPhase.ABORTED
        state.completed_at = datetime.utcnow()
        state.history.append(
            BuildHistoryEvent(
                phase=BuildPhase.ABORTED,
                action="build_aborted",
                details={},
            )
        )
        await self.storage.save(state)
        logger.info("Build %s aborted", build_id)
        return state

    async def _auto_step(self, state: BuildState, user_message: Optional[str] = None) -> BuildState:
        if state.phase == BuildPhase.PLANNING:
            return await self._plan_step(state)
        if state.phase == BuildPhase.IMPLEMENTING:
            return await self._implement_step(state, user_message)
        if state.phase == BuildPhase.VERIFYING:
            return await self._verify_step(state)
        if state.phase == BuildPhase.REVIEWING:
            return await self._review_step(state)
        if state.phase == BuildPhase.ITERATING:
            return await self._iterate_step(state, user_message)
        return state
```

**Dependencies**: None (depends on Phases 1-3)
**Parallelizable**: No

---

### Task 4.2: Implement Planning Phase

**Description**: Implement `_plan_step` to create BuildGraph and pick first task

**File: `backend/app/services/build_runtime/orchestrator.py` (part 2)**

```python
    async def _plan_step(self, state: BuildState) -> BuildState:
        if not state.build_graph:
            logger.info("Build %s: Creating BuildGraph", state.build_id)
            try:
                result = await self.planner.run(
                    brief=state.brief.model_dump(mode="json"),
                    build_plan=state.build_plan.model_dump(mode="json") if state.build_plan else {},
                    product_doc=state.product_doc.model_dump(mode="json") if state.product_doc else {},
                )
                self._record_agent_usage(state, "PlannerAgent", result)
                graph = BuildGraph.model_validate(result.output)
                state.build_graph = graph
                state.history.append(BuildHistoryEvent(
                    phase=BuildPhase.PLANNING,
                    action="build_graph_created",
                    details={"task_count": len(graph.tasks)}
                ))
            except Exception as exc:
                logger.exception("Build %s: Planner failed", state.build_id)
                state.phase = BuildPhase.ERROR
                state.history.append(BuildHistoryEvent(
                    phase=BuildPhase.PLANNING,
                    action="planner_failed",
                    details={"error": str(exc)}
                ))
                await self.storage.save(state)
                return state

        next_task = self._pick_next_task(state)
        if next_task:
            state.current_task_id = next_task.id
            next_task.status = TaskStatus.DOING
            state.phase = BuildPhase.IMPLEMENTING

            state.history.append(BuildHistoryEvent(
                phase=BuildPhase.PLANNING,
                action="task_selected",
                details={"task_id": next_task.id, "task_title": next_task.title}
            ))
        else:
            # No more tasks - build is complete
            state.phase = BuildPhase.READY
            state.completed_at = datetime.utcnow()

            state.history.append(BuildHistoryEvent(
                phase=BuildPhase.PLANNING,
                action="no_more_tasks",
                details={}
            ))

        await self.storage.save(state)
        return state

    def _pick_next_task(self, state: BuildState) -> Optional[Task]:
        if not state.build_graph:
            return None

        done_ids = {t.id for t in state.build_graph.tasks if t.status == TaskStatus.DONE}

        for task in state.build_graph.tasks:
            if task.status == TaskStatus.TODO:
                if all(dep in done_ids for dep in task.depends_on):
                    return task

        return None
```

**Dependencies**: Task 4.1
**Parallelizable**: No

---

### Task 4.3: Implement Implementation Phase

**Description**: Implement `_implement_step` to generate and apply patches

**File: `backend/app/services/build_runtime/orchestrator.py` (part 3)**

```python
    async def _implement_step(
        self,
        state: BuildState,
        user_message: Optional[str] = None
    ) -> BuildState:
        task = state.get_current_task()
        if not task:
            logger.warning("Build %s: No current task", state.build_id)
            state.phase = BuildPhase.READY
            state.completed_at = datetime.utcnow()
            await self.storage.save(state)
            return state

        logger.info("Build %s: Implementing task %s", state.build_id, task.id)

        # Get relevant files for context
        relevant_files = await self._get_relevant_files(task)

        context: Dict[str, str] = {}
        if user_message:
            context["reviewer_feedback"] = user_message

        try:
            result = await self.implementer.run(
                task=task.model_dump(mode="json"),
                state=state.model_dump(mode="json"),
                relevant_files=relevant_files,
                context=context
            )
            self._record_agent_usage(state, "ImplementerAgent", result)
            patch = PatchSet.model_validate(result.output)
            patch.task_id = task.id

            state.last_patch = patch
            state.patch_sets.append(patch)

            state.history.append(BuildHistoryEvent(
                phase=BuildPhase.IMPLEMENTING,
                action="patch_generated",
                details={
                    "task_id": task.id,
                    "patch_id": patch.id,
                    "touched_files": patch.touched_files
                }
            ))

        except Exception as exc:
            logger.exception("Build %s: Implementer failed", state.build_id)
            state.history.append(BuildHistoryEvent(
                phase=BuildPhase.IMPLEMENTING,
                action="implementer_failed",
                details={"error": str(exc)}
            ))
            await self.storage.save(state)
            return state

        try:
            apply_result = await self.repo_tools.apply_patch(patch.diff)

            if apply_result["applied"]:
                state.history.append(BuildHistoryEvent(
                    phase=BuildPhase.IMPLEMENTING,
                    action="patch_applied",
                    details={"touched": apply_result["touched"]}
                ))

                snapshot_tools = self.snapshot_tools or SnapshotTools(state.project_id)
                try:
                    await snapshot_tools.create(
                        reason=f"After task {task.id}: {task.title}",
                        metadata={"patch_id": patch.id}
                    )
                except Exception:
                    logger.warning("Build %s: Snapshot creation failed", state.build_id)

                state.phase = BuildPhase.VERIFYING

            else:
                state.history.append(BuildHistoryEvent(
                    phase=BuildPhase.IMPLEMENTING,
                    action="patch_failed",
                    details={"errors": apply_result.get("errors", [])}
                ))

        except Exception as exc:
            logger.exception("Build %s: Patch apply failed", state.build_id)
            state.history.append(BuildHistoryEvent(
                phase=BuildPhase.IMPLEMENTING,
                action="patch_apply_failed",
                details={"error": str(exc)}
            ))

        await self.storage.save(state)
        return state

    async def _get_relevant_files(self, task: Task) -> Dict[str, str]:
        files: Dict[str, str] = {}
        for path in task.files_expected[:5]:
            try:
                files[path] = await self.repo_tools.read(path)
            except FileNotFoundError:
                files[path] = ""
            except Exception as exc:
                files[path] = f"[Error reading {path}: {exc}]"
        return files
```

**Dependencies**: Task 4.1
**Parallelizable**: No

---

### Task 4.4: Implement Verification Phase

**Description**: Implement `_verify_step` to run validation and checks concurrently (draft pages when available)

**File: `backend/app/services/build_runtime/orchestrator.py` (part 4)**

```python
    async def _verify_step(self, state: BuildState) -> BuildState:
        logger.info("Build %s: Verifying", state.build_id)

        pages = await self._get_draft_pages(state)
        validation_task = asyncio.create_task(self._validate_pages(pages))
        checks_task = asyncio.create_task(self.check_tools.all())

        validation_result, checks_result = await asyncio.gather(
            validation_task, checks_task, return_exceptions=True
        )

        if isinstance(validation_result, Exception):
            logger.exception("Build %s: Validation failed", state.build_id)
            validation = ValidationReport(
                ok=False,
                errors=[f"Validation error: {validation_result}"],
                warnings=[],
                normalized_html=None,
                js_valid=False,
            )
        else:
            validation = validation_result

        state.last_validation = validation
        state.validation_reports.append(validation)
        state.history.append(
            BuildHistoryEvent(
                phase=BuildPhase.VERIFYING,
                action="validation_complete",
                details={"ok": validation.ok, "error_count": len(validation.errors)},
            )
        )

        if isinstance(checks_result, Exception):
            logger.exception("Build %s: Checks failed", state.build_id)
            checks = CheckReport(
                ok=False,
                typecheck_ok=False,
                lint_ok=False,
                unit_ok=False,
                logs=f"Check error: {checks_result}",
            )
        else:
            checks = checks_result

        state.last_checks = checks
        state.check_reports.append(checks)
        state.history.append(
            BuildHistoryEvent(
                phase=BuildPhase.VERIFYING,
                action="checks_complete",
                details={
                    "ok": checks.ok,
                    "typecheck_ok": checks.typecheck_ok,
                    "lint_ok": checks.lint_ok,
                    "unit_ok": checks.unit_ok,
                },
            )
        )

        state.phase = BuildPhase.REVIEWING

        await self.storage.save(state)
        return state
```

**Dependencies**: Task 4.1
**Parallelizable**: No

---

### Task 4.5: Implement Review Phase

**Description**: Implement `_review_step` to get reviewer decision

**File: `backend/app/services/build_runtime/orchestrator.py` (part 5)**

```python
    async def _review_step(self, state: BuildState) -> BuildState:
        """Call ReviewerAgent to get decision."""
        task = state.get_current_task()
        if not task:
            state.phase = BuildPhase.READY
            state.completed_at = datetime.utcnow()
            await self.storage.save(state)
            return state

        logger.info("Build %s: Reviewing task %s", state.build_id, task.id)

        try:
            result = await self.reviewer.run(
                task=task.model_dump(mode="json"),
                patchset=state.last_patch.model_dump(mode="json") if state.last_patch else None,
                validation_report=(
                    state.last_validation.model_dump(mode="json") if state.last_validation else None
                ),
                check_report=state.last_checks.model_dump(mode="json") if state.last_checks else None,
                acceptance_criteria=task.acceptance
            )
            self._record_agent_usage(state, "ReviewerAgent", result)
            review = ReviewReport.model_validate(result.output)

            state.last_review = review
            state.review_reports.append(review)

            state.history.append(BuildHistoryEvent(
                phase=BuildPhase.REVIEWING,
                action=review.decision.value,
                details={
                    "task_id": task.id,
                    "reasons": review.reasons,
                    "required_fixes": review.required_fixes
                }
            ))

        except Exception as exc:
            logger.exception("Build %s: Reviewer failed", state.build_id)
            # Default to request changes on error
            review = ReviewReport(
                decision=ReviewDecision.REQUEST_CHANGES,
                reasons=[f"Reviewer error: {str(exc)}"],
                required_fixes=["Retry review"]
            )
            state.last_review = review

        # Handle decision
        if state.last_review.decision == ReviewDecision.APPROVE:
            # Mark task done
            task.status = TaskStatus.DONE
            task.completed_at = datetime.utcnow()

            if state.all_tasks_done:
                state.phase = BuildPhase.READY
                state.completed_at = datetime.utcnow()

                state.history.append(
                    BuildHistoryEvent(
                        phase=BuildPhase.REVIEWING,
                        action="build_complete",
                        details={"total_tasks": len(state.build_graph.tasks) if state.build_graph else 0},
                    )
                )
            else:
                # Pick next task
                state.current_task_id = None
                state.phase = BuildPhase.PLANNING

        else:
            # Request changes - go to iterating
            state.phase = BuildPhase.ITERATING

        await self.storage.save(state)
        return state
```

**Dependencies**: Task 4.1
**Parallelizable**: No

---

### Task 4.6: Implement Iteration Phase

**Description**: Implement `_iterate_step` to handle reviewer feedback

**File: `backend/app/services/build_runtime/orchestrator.py` (part 6)**

```python
    async def _iterate_step(
        self,
        state: BuildState,
        user_message: Optional[str] = None
    ) -> BuildState:
        # Build feedback message from reviewer
        feedback_parts: list[str] = []
        if state.last_review:
            feedback_parts.append("Reviewer feedback:")
            feedback_parts.extend([f"- {r}" for r in state.last_review.reasons])
            if state.last_review.required_fixes:
                feedback_parts.append("Required fixes:")
                feedback_parts.extend([f"- {f}" for f in state.last_review.required_fixes])

        if user_message:
            feedback_parts.append(f"\nUser message: {user_message}")

        feedback = "\n".join(feedback_parts) if feedback_parts else None

        state.history.append(BuildHistoryEvent(
            phase=BuildPhase.ITERATING,
            action="iteration_started",
            details={"feedback_provided": bool(feedback)}
        ))

        # Return to implementing with feedback
        state.phase = BuildPhase.IMPLEMENTING

        await self.storage.save(state)

        # Continue to implementing
        return await self._implement_step(state, feedback)
```

**Dependencies**: Task 4.1
**Parallelizable**: No

---

### Task 4.6b: Agent Usage + Draft Validation Helpers

**Description**: Track agent usage and aggregate validation across draft pages

**File: `backend/app/services/build_runtime/orchestrator.py` (helpers)**

```python
    def _record_agent_usage(self, state: BuildState, agent_name: str, result) -> None:
        token_usage = getattr(result, "token_usage", None)
        usage = TokenUsage(
            prompt_tokens=getattr(token_usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(token_usage, "completion_tokens", 0) or 0,
            total_tokens=getattr(token_usage, "total_tokens", 0) or 0,
        )
        model_name = getattr(result, "model", "unknown")
        entry = AgentUsage(agent=agent_name, model=model_name, usage=usage)
        state.last_agent_usage = entry
        state.agent_usage.append(entry)
        state.history.append(
            BuildHistoryEvent(
                phase=state.phase,
                action="agent_usage_recorded",
                details={
                    "agent": agent_name,
                    "model": model_name,
                    "usage": entry.usage.model_dump(mode="json"),
                },
            )
        )

    async def _get_draft_pages(self, state: BuildState) -> list:
        db = getattr(self.storage, "db", None)
        if db is None:
            return []
        try:
            from app.services.draft_service import DraftService

            service = DraftService(db)
            return await service.get_draft_pages(UUID(state.project_id), UUID(state.user_id))
        except Exception as exc:
            logger.warning("Build %s: Unable to load draft pages (%s)", state.build_id, exc)
            return []

    async def _validate_pages(self, pages: list) -> ValidationReport:
        if not pages:
            return await self.validate_tools.run("")

        if len(pages) == 1:
            page = pages[0]
            return await self.validate_tools.run(page.html or "", page.js)

        reports = await asyncio.gather(
            *[self.validate_tools.run(page.html or "", page.js) for page in pages],
            return_exceptions=True,
        )

        errors: list[str] = []
        warnings: list[str] = []
        js_valid = True
        normalized_html = None

        for page, report in zip(pages, reports):
            page_ref = getattr(page, "slug", "page")
            if isinstance(report, Exception):
                errors.append(f"{page_ref}: validation error: {report}")
                js_valid = False
                continue
            if report.errors:
                errors.extend([f"{page_ref}: {err}" for err in report.errors])
            if report.warnings:
                warnings.extend([f"{page_ref}: {warn}" for warn in report.warnings])
            js_valid = js_valid and report.js_valid
            if normalized_html is None and report.normalized_html:
                normalized_html = report.normalized_html

        return ValidationReport(
            ok=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_html=normalized_html,
            js_valid=js_valid,
        )
```

**Dependencies**: Task 4.1
**Parallelizable**: No

---

### Task 4.7: Wire Orchestrator to API

**Description**: Connect orchestrator to API endpoints

**File: `backend/app/api/build.py` (updates)**

```python
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import get_current_user
from app.services.build_runtime.storage import BuildStorage
from app.services.build_runtime.orchestrator import BuildOrchestrator


@router.post("/start", response_model=BuildResponse)
async def start_build(
    req: StartBuildRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> BuildResponse:
    try:
        project_uuid = UUID(req.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id")

    user_id = await _resolve_user_id(user, db)
    await _ensure_project_access(project_uuid, user_id, db)

    orchestrator = BuildOrchestrator(storage=BuildStorage(db))
    try:
        state = await orchestrator.start(
            project_id=str(project_uuid),
            user_id=str(user_id),
            brief=req.seed.get("brief", {}),
            build_plan=req.seed.get("build_plan"),
            product_doc=req.seed.get("product_doc"),
        )
        return _state_to_response(state)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start build: {str(exc)}",
        )
```

**Dependencies**: Tasks 4.1-4.6
**Parallelizable**: No

---

## Technical Considerations

### Key Dependencies
- All models from Phase 1
- All tools from Phase 2
- All agents from Phase 3
- Database session for storage

### Architecture Decisions
1. **Dependency injection** - All dependencies injected for testability
2. **One step per call** - API calls advance by one phase transition
3. **Auto mode** - Optional full loop in single call
4. **Error resilience** - Orchestrator continues on individual failures
5. **Usage tracking** - Agent token usage recorded per agent run

### State Machine Design
- Each phase has clear entry/exit conditions
- History recorded for debugging
- Terminal states prevent further steps

### Concurrency
- Steps are async for I/O operations
- Validation and checks run in parallel within verify step
- No concurrent steps on same build (single API call at a time)

---

## Acceptance Criteria

- [ ] `orchestrator.start()` creates build in 'planning' phase
- [ ] `orchestrator.step()` advances through phases correctly
- [ ] Planning phase creates BuildGraph and picks task
- [ ] Implementing phase generates and applies patch
- [ ] Verifying phase runs validation and checks (draft pages when available)
- [ ] Reviewing phase gets reviewer decision
- [ ] Iterating phase handles reviewer feedback
- [ ] Ready phase marks build complete
- [ ] `abort()` sets phase to 'aborted'
- [ ] History is recorded for each transition
- [ ] Agent usage is recorded for planner/implementer/reviewer runs
- [ ] State persists after each step
- [ ] Error handling doesn't crash orchestrator
- [ ] Tests cover all phase transitions

---

## Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| State inconsistency on error | Medium | Medium | Atomic save after each step |
| Infinite loop in iterating | Low | Medium | Max iteration counter |
| Step timeout on long operations | Medium | Low | Async timeouts on tools |
| Memory growth from history | Low | Low | Prune old history entries |
| Draft page fetch failures | Low | Low | Fall back to empty validation input |

---

## Estimated Scope

**Complexity**: Large

**Key Effort Drivers**:
- Implementing all 6 phase transitions
- Error handling across all paths
- Integration with tools and agents
- Comprehensive testing

**Estimated Lines of Code**: ~500-800 (orchestrator + API integration)

---

## Testing Strategy

### Unit Tests
- Test each phase transition in isolation
- Test task picking logic
- Test history recording
- Test error handling

### Integration Tests
- (Pending) Add full auto step from planning to ready
- (Pending) Add iterating with reviewer feedback
- (Pending) Add abort at various phases

### Test Files
- `backend/tests/test_build_runtime_orchestrator.py`
