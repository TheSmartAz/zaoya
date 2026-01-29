"""Build Orchestrator - State machine for the agentic build loop."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Callable, Dict, Optional
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
from .events import BuildEvent, BuildEventEmitter

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
        event_sink: Callable[[BuildEvent], None] | None = None,
        event_emitter: BuildEventEmitter | None = None,
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
        self.event_sink = event_sink
        self.event_emitter = event_emitter or BuildEventEmitter()
        self._emitted_pages: set[str] = set()

    def _emit(self, event: BuildEvent) -> None:
        if self.event_sink:
            self.event_sink(event)

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

    async def _plan_step(self, state: BuildState) -> BuildState:
        if not state.build_graph:
            logger.info("Build %s: Creating BuildGraph", state.build_id)
            try:
                self._emit(
                    self.event_emitter.agent_thinking(
                        f"agent-planner-{uuid4().hex}",
                        "PlannerAgent: analyzing requirements",
                    )
                )
                result = await self.planner.run(
                    brief=state.brief.model_dump(mode="json"),
                    build_plan=state.build_plan.model_dump(mode="json") if state.build_plan else {},
                    product_doc=state.product_doc.model_dump(mode="json") if state.product_doc else {},
                )
                self._record_agent_usage(state, "PlannerAgent", result)
                graph = BuildGraph.model_validate(result.output)
                state.build_graph = graph
                if state.build_plan:
                    pages = [
                        {"id": page.id, "name": page.name, "path": page.path}
                        for page in state.build_plan.pages
                    ]
                    features = list(state.build_plan.features or [])
                    design_system = dict(state.build_plan.design_system or {})
                    estimated_complexity = state.build_plan.estimated_complexity
                else:
                    pages = []
                    features = []
                    design_system = {}
                    estimated_complexity = None
                tasks = [
                    {"id": task.id, "title": task.title, "status": task.status.value}
                    for task in graph.tasks
                ]
                self._emit(
                    self.event_emitter.build_plan_card(
                        pages,
                        tasks,
                        len(graph.tasks),
                        features=features,
                        design_system=design_system,
                        estimated_complexity=estimated_complexity,
                    )
                )
                state.history.append(
                    BuildHistoryEvent(
                        phase=BuildPhase.PLANNING,
                        action="build_graph_created",
                        details={"task_count": len(graph.tasks)},
                    )
                )
            except Exception as exc:
                logger.exception("Build %s: Planner failed", state.build_id)
                state.phase = BuildPhase.ERROR
                state.history.append(
                    BuildHistoryEvent(
                        phase=BuildPhase.PLANNING,
                        action="planner_failed",
                        details={"error": str(exc)},
                    )
                )
                await self.storage.save(state)
                return state

        next_task = self._pick_next_task(state)
        if next_task:
            state.current_task_id = next_task.id
            next_task.status = TaskStatus.DOING
            state.phase = BuildPhase.IMPLEMENTING
            self._emit(self.event_emitter.task_started(next_task.id, next_task.title))
            state.history.append(
                BuildHistoryEvent(
                    phase=BuildPhase.PLANNING,
                    action="task_selected",
                    details={"task_id": next_task.id, "task_title": next_task.title},
                )
            )
        else:
            state.phase = BuildPhase.READY
            state.completed_at = datetime.utcnow()
            self._emit(self.event_emitter.build_complete())
            state.history.append(
                BuildHistoryEvent(
                    phase=BuildPhase.PLANNING,
                    action="no_more_tasks",
                    details={},
                )
            )

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

    async def _implement_step(self, state: BuildState, user_message: Optional[str] = None) -> BuildState:
        task = state.get_current_task()
        if not task:
            logger.warning("Build %s: No current task", state.build_id)
            state.phase = BuildPhase.READY
            state.completed_at = datetime.utcnow()
            await self.storage.save(state)
            return state

        logger.info("Build %s: Implementing task %s", state.build_id, task.id)

        relevant_files = await self._get_relevant_files(task)
        context: Dict[str, str] = {}
        if user_message:
            context["reviewer_feedback"] = user_message

        try:
            self._emit(
                self.event_emitter.agent_thinking(
                    f"agent-implementer-{uuid4().hex}",
                    f"ImplementerAgent: {task.title}",
                )
            )
            result = await self.implementer.run(
                task=task.model_dump(mode="json"),
                state=state.model_dump(mode="json"),
                relevant_files=relevant_files,
                context=context,
            )
            self._record_agent_usage(state, "ImplementerAgent", result)
            patch = PatchSet.model_validate(result.output)
            patch.task_id = task.id
            state.last_patch = patch
            state.patch_sets.append(patch)
            state.history.append(
                BuildHistoryEvent(
                    phase=BuildPhase.IMPLEMENTING,
                    action="patch_generated",
                    details={
                        "task_id": task.id,
                        "patch_id": patch.id,
                        "touched_files": patch.touched_files,
                    },
                )
            )
        except Exception as exc:
            logger.exception("Build %s: Implementer failed", state.build_id)
            self._emit(self.event_emitter.task_failed(task.id, task.title, error=str(exc)))
            task.status = TaskStatus.BLOCKED
            state.phase = BuildPhase.ERROR
            state.completed_at = datetime.utcnow()
            state.history.append(
                BuildHistoryEvent(
                    phase=BuildPhase.IMPLEMENTING,
                    action="implementer_failed",
                    details={"error": str(exc)},
                )
            )
            await self.storage.save(state)
            return state

        try:
            apply_result = await self.repo_tools.apply_patch(patch.diff)
            if apply_result["applied"]:
                state.history.append(
                    BuildHistoryEvent(
                        phase=BuildPhase.IMPLEMENTING,
                        action="patch_applied",
                        details={"touched": apply_result["touched"]},
                    )
                )

                snapshot_tools = self.snapshot_tools or SnapshotTools(state.project_id)
                try:
                    await snapshot_tools.create(
                        reason=f"After task {task.id}: {task.title}",
                        metadata={"patch_id": patch.id},
                    )
                except Exception:
                    logger.warning("Build %s: Snapshot creation failed", state.build_id)

                state.phase = BuildPhase.VERIFYING
            else:
                state.history.append(
                    BuildHistoryEvent(
                        phase=BuildPhase.IMPLEMENTING,
                        action="patch_failed",
                        details={"errors": apply_result.get("errors", [])},
                    )
                )
        except Exception as exc:
            logger.exception("Build %s: Patch apply failed", state.build_id)
            state.history.append(
                BuildHistoryEvent(
                    phase=BuildPhase.IMPLEMENTING,
                    action="patch_apply_failed",
                    details={"error": str(exc)},
                )
            )

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

    async def _verify_step(self, state: BuildState) -> BuildState:
        logger.info("Build %s: Verifying", state.build_id)

        pages = await self._get_draft_pages(state)
        for page in pages:
            page_id = str(page.id)
            if page_id in self._emitted_pages:
                continue
            self._emitted_pages.add(page_id)
            path = f"/p/{page.slug}" if page.slug else "/"
            self._emit(self.event_emitter.page_card(page_id, page.title, path))
            self._emit(self.event_emitter.preview_update(page_id))
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
        if not validation.ok:
            errors = (
                validation.error_details
                if validation.error_details
                else [{"type": "validation", "message": err} for err in validation.errors]
            )
            suggestions = validation.warnings or []
            self._emit(self.event_emitter.validation_card(errors, suggestions))

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

    async def _review_step(self, state: BuildState) -> BuildState:
        task = state.get_current_task()
        if not task:
            state.phase = BuildPhase.READY
            state.completed_at = datetime.utcnow()
            await self.storage.save(state)
            return state

        logger.info("Build %s: Reviewing task %s", state.build_id, task.id)

        try:
            self._emit(
                self.event_emitter.agent_thinking(
                    f"agent-reviewer-{uuid4().hex}",
                    "ReviewerAgent: reviewing changes",
                )
            )
            result = await self.reviewer.run(
                task=task.model_dump(mode="json"),
                patchset=state.last_patch.model_dump(mode="json") if state.last_patch else None,
                validation_report=(
                    state.last_validation.model_dump(mode="json") if state.last_validation else None
                ),
                check_report=state.last_checks.model_dump(mode="json") if state.last_checks else None,
                acceptance_criteria=task.acceptance,
            )
            self._record_agent_usage(state, "ReviewerAgent", result)
            review = ReviewReport.model_validate(result.output)
            state.last_review = review
            state.review_reports.append(review)
            state.history.append(
                BuildHistoryEvent(
                    phase=BuildPhase.REVIEWING,
                    action=review.decision.value,
                    details={
                        "task_id": task.id,
                        "reasons": review.reasons,
                        "required_fixes": review.required_fixes,
                    },
                )
            )
        except Exception as exc:
            logger.exception("Build %s: Reviewer failed", state.build_id)
            review = ReviewReport(
                decision=ReviewDecision.REQUEST_CHANGES,
                reasons=[f"Reviewer error: {str(exc)}"],
                required_fixes=["Retry review"],
            )
            state.last_review = review

        if state.last_review.decision == ReviewDecision.APPROVE:
            task.status = TaskStatus.DONE
            task.completed_at = datetime.utcnow()
            self._emit(self.event_emitter.task_done(task.id, task.title))

            if state.all_tasks_done:
                state.phase = BuildPhase.READY
                state.completed_at = datetime.utcnow()
                self._emit(self.event_emitter.build_complete())
                state.history.append(
                    BuildHistoryEvent(
                        phase=BuildPhase.REVIEWING,
                        action="build_complete",
                        details={"total_tasks": len(state.build_graph.tasks) if state.build_graph else 0},
                    )
                )
            else:
                state.current_task_id = None
                state.phase = BuildPhase.PLANNING
        else:
            state.phase = BuildPhase.ITERATING

        await self.storage.save(state)
        return state

    async def _iterate_step(self, state: BuildState, user_message: Optional[str] = None) -> BuildState:
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
        state.history.append(
            BuildHistoryEvent(
                phase=BuildPhase.ITERATING,
                action="iteration_started",
                details={"feedback_provided": bool(feedback)},
            )
        )
        state.phase = BuildPhase.IMPLEMENTING
        await self.storage.save(state)
        return await self._implement_step(state, feedback)

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
            slug = getattr(page, "slug", None) or "page"
            html_path = f"pages/{slug}.html"
            js_path = f"pages/{slug}.js"
            return await self.validate_tools.run(
                page.html or "",
                page.js,
                html_path=html_path,
                js_path=js_path,
            )

        reports = await asyncio.gather(
            *[
                self.validate_tools.run(
                    page.html or "",
                    page.js,
                    html_path=f"pages/{getattr(page, 'slug', None) or 'page'}.html",
                    js_path=f"pages/{getattr(page, 'slug', None) or 'page'}.js",
                )
                for page in pages
            ],
            return_exceptions=True,
        )

        errors: list[str] = []
        warnings: list[str] = []
        js_valid = True
        normalized_html = None
        error_details: list[dict] = []

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
            if report.error_details:
                error_details.extend(report.error_details)

        return ValidationReport(
            ok=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            error_details=error_details,
            normalized_html=normalized_html,
            js_valid=js_valid,
        )
