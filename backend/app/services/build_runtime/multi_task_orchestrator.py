"""Multi-page build orchestrator that generates pages sequentially."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, List, Optional
import re
import uuid

from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models.db import Project, ProjectPage
from app.models.db.build_plan import BuildPlan as DbBuildPlan, BuildStatus
from app.services.ai_service import generate_response, resolve_available_model
from app.services.validator import validate_html, validate_js_with_details
from app.services.build_runtime.events import BuildEvent, BuildEventEmitter, BuildEventType
from app.services.build_runtime.planner import PageSpec
from app.services.build_runtime.plan_generator import BuildPlanGenerator
from app.services.thumbnail_queue import thumbnail_queue
from app.services.version_service import VersionService, _snapshot_from_pages


@dataclass
class BuildSession:
    """Active build session state."""

    id: str
    project_id: str
    user_id: str
    pages: List[PageSpec]
    completed_pages: List[str] = field(default_factory=list)
    failed_pages: List[str] = field(default_factory=list)
    failed_page_errors: dict[str, list[dict]] = field(default_factory=dict)
    project_error_details: list[dict] = field(default_factory=list)
    is_cancelled: bool = False
    final_checks_failed: bool = False
    build_plan_id: Optional[str] = None
    task_mapping: dict[str, str] = field(default_factory=dict)
    page_html: dict[str, str] = field(default_factory=dict)
    retry_counts: dict[str, int] = field(default_factory=dict)
    last_failed_attempt_id: Optional[str] = None

    def cancel(self) -> None:
        self.is_cancelled = True


class MultiTaskOrchestrator:
    """Orchestrates multi-page generation with real-time streaming."""

    def __init__(self, model: Optional[str] = None) -> None:
        self.model = resolve_available_model(model)
        self.emitter = BuildEventEmitter()
        self.sessions: dict[str, BuildSession] = {}
        self.plan_generator = BuildPlanGenerator()
        self.max_page_retries = 3

    async def start_build(
        self,
        project_id: str,
        user_id: str,
        pages: List[PageSpec],
        product_doc: object,
    ) -> str:
        session_id = str(uuid.uuid4())
        session = BuildSession(
            id=session_id,
            project_id=project_id,
            user_id=user_id,
            pages=pages,
        )
        self.sessions[session_id] = session
        try:
            plan = await self.create_build_plan(
                project_id=project_id,
                pages=pages,
                product_doc=product_doc,
                plan_id=session_id,
            )
            if plan:
                session.build_plan_id = str(plan.id)
                session.task_mapping = self._build_task_mapping(plan, pages)
        except Exception:
            # Build can proceed even if plan creation fails
            pass
        return session_id

    async def create_build_plan(
        self,
        project_id: str,
        pages: List[PageSpec],
        product_doc: object,
        plan_id: Optional[str] = None,
    ) -> Optional[DbBuildPlan]:
        """Create and persist a BuildPlan for this build."""
        plan = self.plan_generator.generate(
            project_id=project_id,
            pages=pages,
            product_doc=product_doc,
            plan_id=plan_id,
        )

        now = datetime.utcnow()
        now_ts = now.timestamp()

        # Mark planning tasks as complete since plan generation already happened.
        tasks = list(plan.tasks or [])
        for task in tasks:
            if task.get("category") == "planning":
                task["status"] = "done"
                task["started_at"] = task.get("started_at") or now_ts
                task["completed_at"] = task.get("completed_at") or now_ts

        plan.tasks = tasks
        plan.completed_tasks = sum(1 for t in tasks if t.get("status") == "done")
        plan.failed_tasks = sum(1 for t in tasks if t.get("status") == "failed")
        plan.status = BuildStatus.RUNNING
        plan.started_at = now

        async with AsyncSessionLocal() as db:
            db.add(plan)
            await db.commit()
            await db.refresh(plan)
            return plan

    async def _apply_plan_updates(
        self,
        plan_id: str,
        updates: List[dict],
    ) -> Optional[dict]:
        if not updates:
            return None

        try:
            plan_uuid = UUID(plan_id)
        except ValueError:
            return None

        async with AsyncSessionLocal() as db:
            plan = await db.get(DbBuildPlan, plan_uuid)
            if not plan:
                return None

            tasks = list(plan.tasks or [])
            now_ts = datetime.utcnow().timestamp()

            for update in updates:
                task_id = update.get("id")
                status = update.get("status")
                if not task_id or not status:
                    continue
                for task in tasks:
                    if task.get("id") != task_id:
                        continue
                    task["status"] = status
                    if status == "running":
                        if not task.get("started_at"):
                            task["started_at"] = now_ts
                    elif status in {"done", "failed", "skipped"}:
                        task["completed_at"] = now_ts
                    if update.get("error"):
                        task["error"] = update["error"]
                    break

            plan.tasks = tasks
            plan.completed_tasks = sum(1 for t in tasks if t.get("status") == "done")
            plan.failed_tasks = sum(1 for t in tasks if t.get("status") == "failed")

            await db.commit()
            await db.refresh(plan)

            return {
                "id": str(plan.id),
                "completed_tasks": plan.completed_tasks,
                "failed_tasks": plan.failed_tasks,
                "tasks": plan.tasks or [],
                "status": plan.status.value,
            }

    async def _set_plan_status(
        self,
        plan_id: str,
        status: BuildStatus,
    ) -> Optional[dict]:
        try:
            plan_uuid = UUID(plan_id)
        except ValueError:
            return None

        async with AsyncSessionLocal() as db:
            plan = await db.get(DbBuildPlan, plan_uuid)
            if not plan:
                return None

            now = datetime.utcnow()
            plan.status = status
            if status == BuildStatus.RUNNING and not plan.started_at:
                plan.started_at = now
            if status in {BuildStatus.COMPLETED, BuildStatus.FAILED, BuildStatus.CANCELLED}:
                plan.completed_at = now
                if plan.started_at:
                    delta = now - plan.started_at
                    plan.actual_duration_ms = int(delta.total_seconds() * 1000)

            await db.commit()
            await db.refresh(plan)

            return {
                "id": str(plan.id),
                "completed_tasks": plan.completed_tasks,
                "failed_tasks": plan.failed_tasks,
                "tasks": plan.tasks or [],
                "status": plan.status.value,
            }

    def _build_task_mapping(
        self,
        plan: DbBuildPlan,
        pages: List[PageSpec],
    ) -> dict[str, str]:
        """Map runtime task keys to BuildPlan task IDs."""
        mapping: dict[str, str] = {}
        plan_tasks = plan.tasks or []

        for plan_task in plan_tasks:
            if plan_task.get("page_id"):
                continue
            name = plan_task.get("name", "")
            if "创建构建计划" in name:
                mapping["project-plan"] = plan_task.get("id", "")
            elif "解析需求文档" in name:
                mapping["project-doc"] = plan_task.get("id", "")
            elif "跨页面" in name or "链接" in name:
                mapping["project-links"] = plan_task.get("id", "")
            elif "最终检查" in name:
                mapping["project-final"] = plan_task.get("id", "")

        for page in pages:
            for plan_task in plan_tasks:
                if plan_task.get("page_id") != page.id:
                    continue
                name = plan_task.get("name", "")
                if "HTML" in name and "生成" in name:
                    mapping[f"page-{page.id}"] = plan_task.get("id", "")
                elif "样式" in name:
                    mapping[f"style-{page.id}"] = plan_task.get("id", "")
                elif "HTML" in name and "验证" in name:
                    mapping[f"validate-{page.id}"] = plan_task.get("id", "")
                elif "安全" in name:
                    mapping[f"secure-{page.id}"] = plan_task.get("id", "")
                elif "保存" in name:
                    mapping[f"save-{page.id}"] = plan_task.get("id", "")
                elif "缩略图" in name:
                    mapping[f"thumb-{page.id}"] = plan_task.get("id", "")

        return {k: v for k, v in mapping.items() if v}

    def _page_task_keys(self, page_id: str) -> List[str]:
        return [
            f"page-{page_id}",
            f"style-{page_id}",
            f"validate-{page_id}",
            f"secure-{page_id}",
            f"save-{page_id}",
            f"thumb-{page_id}",
        ]

    async def _mark_plan_task(
        self,
        session: BuildSession,
        runtime_key: str,
        status: str,
        error: Optional[str] = None,
    ) -> Optional[BuildEvent]:
        if not session.build_plan_id:
            return None
        task_id = session.task_mapping.get(runtime_key)
        if not task_id:
            return None
        plan_snapshot = await self._apply_plan_updates(
            session.build_plan_id,
            [{"id": task_id, "status": status, "error": error}],
        )
        if not plan_snapshot:
            return None
        return BuildEvent(type=BuildEventType.PLAN_UPDATE, plan_data=plan_snapshot)

    async def _mark_plan_tasks(
        self,
        session: BuildSession,
        runtime_keys: List[str],
        status: str,
        error: Optional[str] = None,
    ) -> Optional[BuildEvent]:
        if not session.build_plan_id:
            return None
        updates = []
        for key in runtime_keys:
            task_id = session.task_mapping.get(key)
            if task_id:
                updates.append({"id": task_id, "status": status, "error": error})
        if not updates:
            return None
        plan_snapshot = await self._apply_plan_updates(session.build_plan_id, updates)
        if not plan_snapshot:
            return None
        return BuildEvent(type=BuildEventType.PLAN_UPDATE, plan_data=plan_snapshot)

    async def _complete_project_tasks(self, session: BuildSession) -> List[BuildEvent]:
        events: List[BuildEvent] = []
        if not session.build_plan_id:
            return events

        session.final_checks_failed = False
        session.project_error_details = []

        link_key = "project-links"
        final_key = "project-final"

        if session.failed_pages:
            skip_event = await self._mark_plan_tasks(
                session,
                [link_key, final_key],
                "skipped",
                error="page failures",
            )
            if skip_event:
                events.append(skip_event)
            return events

        running_event = await self._mark_plan_task(session, link_key, "running")
        if running_event:
            events.append(running_event)

        ok, errors = _validate_cross_page_links(session.page_html, session.pages)
        if not ok:
            session.final_checks_failed = True
            session.project_error_details = [
                _build_project_link_error_detail(err) for err in errors
            ]
            failed_event = await self._mark_plan_task(
                session,
                link_key,
                "failed",
                error="; ".join(errors),
            )
            if failed_event:
                events.append(failed_event)
            skip_event = await self._mark_plan_task(
                session,
                final_key,
                "skipped",
                error="link validation failed",
            )
            if skip_event:
                events.append(skip_event)
            return events

        done_event = await self._mark_plan_task(session, link_key, "done")
        if done_event:
            events.append(done_event)

        final_running = await self._mark_plan_task(session, final_key, "running")
        if final_running:
            events.append(final_running)
        final_done = await self._mark_plan_task(session, final_key, "done")
        if final_done:
            events.append(final_done)
        return events

    async def _emit_success_version(self, session: BuildSession) -> List[BuildEvent]:
        events: List[BuildEvent] = []
        try:
            async with AsyncSessionLocal() as db:
                version_service = VersionService(db)
                tasks_completed = [
                    f"Generated {page.name}"
                    for page in session.pages
                    if page.id in session.completed_pages
                ]
                completed_count = len(session.completed_pages) or len(session.pages)
                version = await version_service.create_version_from_project(
                    project_id=UUID(session.project_id),
                    user_id=UUID(session.user_id),
                    description=f"Generated {completed_count} page(s)",
                    tasks_completed=tasks_completed,
                    validation_status="passed",
                )
                snapshot = await version_service.get_version_snapshot(
                    UUID(session.project_id),
                    UUID(session.user_id),
                    version.id,
                )
                pages = snapshot.get("pages", []) if isinstance(snapshot, dict) else []
                home_page = next(
                    (p for p in pages if isinstance(p, dict) and p.get("is_home")),
                    pages[0] if pages else None,
                )
                events.append(
                    self.emitter.version_card(
                        {
                            "id": str(version.id),
                            "created_at": version.created_at.isoformat(),
                            "change_summary": version.change_summary,
                            "validation_status": version.validation_status,
                            "is_pinned": version.is_pinned,
                            "branch_label": version.branch_label,
                            "page_id": home_page.get("id") if isinstance(home_page, dict) else None,
                            "page_name": home_page.get("name") if isinstance(home_page, dict) else None,
                            "page_path": home_page.get("path") if isinstance(home_page, dict) else None,
                        }
                    )
                )
        except Exception:
            return events
        return events

    async def _record_failed_version_attempt(self, session: BuildSession) -> None:
        try:
            async with AsyncSessionLocal() as db:
                project = await db.get(Project, UUID(session.project_id))
                if not project:
                    return
                pages_result = await db.execute(
                    select(ProjectPage)
                    .where(
                        ProjectPage.project_id == project.id,
                        ProjectPage.branch_id == project.active_branch_id,
                    )
                    .order_by(ProjectPage.sort_order)
                )
                pages = list(pages_result.scalars().all())
                snapshot_data = _snapshot_from_pages(pages)
                version_service = VersionService(db)
                retry_of = None
                if session.last_failed_attempt_id:
                    try:
                        retry_of = UUID(session.last_failed_attempt_id)
                    except ValueError:
                        retry_of = None
                validation_errors: list[dict] = []
                for details in session.failed_page_errors.values():
                    if details:
                        validation_errors.extend(details)
                if session.project_error_details:
                    validation_errors.extend(session.project_error_details)

                attempt = await version_service.record_failed_version(
                    project_id=project.id,
                    user_id=UUID(session.user_id),
                    branch_id=project.active_branch_id,
                    description="Build failed",
                    error_message=_build_failed_message(session, validation_errors),
                    snapshot_data=snapshot_data,
                    validation_errors=validation_errors,
                    retry_of=retry_of,
                )
                await db.commit()
                session.last_failed_attempt_id = str(attempt.id)
        except Exception:
            return

    async def stream_progress(
        self,
        session_id: str,
        product_doc: object,
    ) -> AsyncGenerator[BuildEvent, None]:
        session = self.sessions.get(session_id)
        if not session:
            yield self.emitter.task_failed("unknown", "Build session not found")
            return

        if session.build_plan_id and not session.task_mapping:
            try:
                plan_uuid = UUID(session.build_plan_id)
                async with AsyncSessionLocal() as db:
                    plan = await db.get(DbBuildPlan, plan_uuid)
                    if plan:
                        session.task_mapping = self._build_task_mapping(plan, session.pages)
            except ValueError:
                pass

        try:
            main_page = next((p for p in session.pages if p.is_main), session.pages[0])
            other_pages = [p for p in session.pages if p.id != main_page.id]

            async for event in self._generate_page(session, main_page, product_doc, 0):
                yield event
                if session.is_cancelled:
                    yield self.emitter.task_failed(f"page-{main_page.id}", "Build cancelled")
                    if session.build_plan_id:
                        plan_snapshot = await self._set_plan_status(
                            session.build_plan_id,
                            BuildStatus.CANCELLED,
                        )
                        if plan_snapshot:
                            yield BuildEvent(type=BuildEventType.PLAN_UPDATE, plan_data=plan_snapshot)
                    yield self.emitter.build_complete("Build cancelled")
                    return

            for index, page in enumerate(other_pages, start=1):
                if session.is_cancelled:
                    yield self.emitter.task_failed(f"page-{page.id}", "Build cancelled")
                    if session.build_plan_id:
                        plan_snapshot = await self._set_plan_status(
                            session.build_plan_id,
                            BuildStatus.CANCELLED,
                        )
                        if plan_snapshot:
                            yield BuildEvent(type=BuildEventType.PLAN_UPDATE, plan_data=plan_snapshot)
                    yield self.emitter.build_complete("Build cancelled")
                    return
                async for event in self._generate_page(session, page, product_doc, index):
                    yield event

            project_events = await self._complete_project_tasks(session)
            for event in project_events:
                yield event

            final_status = (
                BuildStatus.CANCELLED
                if session.is_cancelled
                else BuildStatus.FAILED
                if (session.failed_pages or session.final_checks_failed)
                else BuildStatus.COMPLETED
            )
            if session.build_plan_id:
                plan_snapshot = await self._set_plan_status(session.build_plan_id, final_status)
                if plan_snapshot:
                    yield BuildEvent(type=BuildEventType.PLAN_UPDATE, plan_data=plan_snapshot)

            if session.failed_pages or session.final_checks_failed:
                await self._record_failed_version_attempt(session)
                if session.failed_pages:
                    yield self.emitter.build_complete(
                        f"Build completed with {len(session.failed_pages)} failed page(s)"
                    )
                else:
                    yield self.emitter.build_complete("Build completed with validation errors")
            else:
                version_events = await self._emit_success_version(session)
                for event in version_events:
                    yield event
                yield self.emitter.build_complete(
                    f"All {len(session.pages)} pages generated"
                )
        finally:
            if session.failed_pages:
                return
            self.sessions.pop(session_id, None)

    async def _generate_page(
        self,
        session: BuildSession,
        page: PageSpec,
        product_doc: object,
        order: int,
    ) -> AsyncGenerator[BuildEvent, None]:
        generate_key = f"page-{page.id}"
        yield self.emitter.task_started(generate_key, f"Generate {page.name} page")
        plan_event = await self._mark_plan_task(session, generate_key, "running")
        if plan_event:
            yield plan_event

        try:
            prompt = self._build_page_prompt(page, product_doc, session)
            response_text = await generate_response(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
            )
            html, js = _extract_html_js(response_text)

            if not html.strip():
                yield self.emitter.task_failed(generate_key, f"{page.name} generation empty")
                plan_event = await self._mark_plan_task(
                    session,
                    generate_key,
                    "failed",
                    error="generation empty",
                )
                if plan_event:
                    yield plan_event
                skip_event = await self._mark_plan_tasks(
                    session,
                    self._page_task_keys(page.id)[1:],
                    "skipped",
                    error="generation failed",
                )
                if skip_event:
                    yield skip_event
                if page.id not in session.failed_pages:
                    session.failed_pages.append(page.id)
                return

            yield self.emitter.task_done(generate_key, f"{page.name} HTML generated")
            plan_event = await self._mark_plan_task(session, generate_key, "done")
            if plan_event:
                yield plan_event

            style_key = f"style-{page.id}"
            yield self.emitter.task_started(style_key, f"应用样式 {page.name}")
            plan_event = await self._mark_plan_task(session, style_key, "running")
            if plan_event:
                yield plan_event
            styled_html = html
            yield self.emitter.task_done(style_key, f"{page.name} 样式完成")
            plan_event = await self._mark_plan_task(session, style_key, "done")
            if plan_event:
                yield plan_event

            validate_key = f"validate-{page.id}"
            yield self.emitter.task_started(validate_key, f"验证 {page.name} HTML")
            plan_event = await self._mark_plan_task(session, validate_key, "running")
            if plan_event:
                yield plan_event
            slug = _slugify(page.name)
            html_path = f"pages/{slug}.html"
            js_path = f"pages/{slug}.js"
            html_result = validate_html(styled_html, path=html_path)
            validation_errors = html_result.get("errors", []) if isinstance(html_result, dict) else []
            validation_details = (
                html_result.get("error_details", []) if isinstance(html_result, dict) else []
            )
            sanitized_html = (
                html_result.get("normalized_html") if isinstance(html_result, dict) else None
            ) or ""
            if validation_errors:
                yield self.emitter.task_failed(validate_key, f"{page.name} validation failed")
                plan_event = await self._mark_plan_task(
                    session,
                    validate_key,
                    "failed",
                    error="; ".join(validation_errors),
                )
                if plan_event:
                    yield plan_event
                session.failed_page_errors[page.id] = validation_details or [
                    {"type": "validation", "message": err} for err in validation_errors
                ]
                yield self.emitter.validation_card(
                    validation_details
                    if validation_details
                    else [{"type": "validation", "message": err} for err in validation_errors],
                    [],
                    page_id=page.id,
                    page_name=page.name,
                    page_path=page.path,
                    retry_count=session.retry_counts.get(page.id, 0),
                )
                skip_event = await self._mark_plan_tasks(
                    session,
                    [f"secure-{page.id}", f"save-{page.id}", f"thumb-{page.id}"],
                    "skipped",
                    error="validation failed",
                )
                if skip_event:
                    yield skip_event
                if page.id not in session.failed_pages:
                    session.failed_pages.append(page.id)
                return

            yield self.emitter.task_done(validate_key, f"{page.name} HTML 验证完成")
            plan_event = await self._mark_plan_task(session, validate_key, "done")
            if plan_event:
                yield plan_event

            secure_key = f"secure-{page.id}"
            yield self.emitter.task_started(secure_key, f"安全检查 {page.name}")
            plan_event = await self._mark_plan_task(session, secure_key, "running")
            if plan_event:
                yield plan_event
            js_valid, js_errors, js_details = (True, [], [])
            if js and js.strip():
                js_valid, js_errors, js_details = validate_js_with_details(js, path=js_path)
            if not js_valid:
                yield self.emitter.task_failed(secure_key, f"{page.name} security check failed")
                plan_event = await self._mark_plan_task(
                    session,
                    secure_key,
                    "failed",
                    error="; ".join(js_errors),
                )
                if plan_event:
                    yield plan_event
                session.failed_page_errors[page.id] = js_details or [
                    {"type": "security", "message": err} for err in js_errors
                ]
                yield self.emitter.validation_card(
                    js_details if js_details else [{"type": "security", "message": err} for err in js_errors],
                    [],
                    page_id=page.id,
                    page_name=page.name,
                    page_path=page.path,
                    retry_count=session.retry_counts.get(page.id, 0),
                )
                skip_event = await self._mark_plan_tasks(
                    session,
                    [f"save-{page.id}", f"thumb-{page.id}"],
                    "skipped",
                    error="security check failed",
                )
                if skip_event:
                    yield skip_event
                if page.id not in session.failed_pages:
                    session.failed_pages.append(page.id)
                return

            yield self.emitter.task_done(secure_key, f"{page.name} 安全检查通过")
            plan_event = await self._mark_plan_task(session, secure_key, "done")
            if plan_event:
                yield plan_event

            save_key = f"save-{page.id}"
            yield self.emitter.task_started(save_key, f"保存 {page.name} 页面")
            plan_event = await self._mark_plan_task(session, save_key, "running")
            if plan_event:
                yield plan_event
            try:
                page_id = await self._save_page(
                    project_id=session.project_id,
                    page=page,
                    html=sanitized_html,
                    js=js or "",
                    order=order,
                    product_doc=product_doc,
                )
            except Exception as exc:  # noqa: BLE001
                yield self.emitter.task_failed(save_key, f"{page.name} save failed")
                plan_event = await self._mark_plan_task(
                    session,
                    save_key,
                    "failed",
                    error=str(exc),
                )
                if plan_event:
                    yield plan_event
                skip_event = await self._mark_plan_task(
                    session,
                    f"thumb-{page.id}",
                    "skipped",
                    error="save failed",
                )
                if skip_event:
                    yield skip_event
                if page.id not in session.failed_pages:
                    session.failed_pages.append(page.id)
                return
            yield self.emitter.task_done(save_key, f"{page.name} 页面已保存")
            plan_event = await self._mark_plan_task(session, save_key, "done")
            if plan_event:
                yield plan_event

            thumb_key = f"thumb-{page.id}"
            yield self.emitter.task_started(
                thumb_key,
                f"生成 {page.name} 缩略图",
            )
            plan_event = await self._mark_plan_task(session, thumb_key, "running")
            if plan_event:
                yield plan_event
            try:
                async with AsyncSessionLocal() as db:
                    await thumbnail_queue.enqueue_thumbnail(
                        db=db,
                        project_id=UUID(session.project_id),
                        page_id=UUID(page_id),
                    )
                yield self.emitter.task_done(
                    thumb_key,
                    f"{page.name} 缩略图已排队",
                )
                plan_event = await self._mark_plan_task(session, thumb_key, "done")
            except Exception as exc:
                yield self.emitter.task_done(
                    thumb_key,
                    f"{page.name} 缩略图跳过",
                )
                plan_event = await self._mark_plan_task(
                    session,
                    thumb_key,
                    "skipped",
                    error=str(exc),
                )
            if plan_event:
                yield plan_event

            session.completed_pages.append(page.id)
            session.page_html[page.id] = sanitized_html
            session.failed_page_errors.pop(page.id, None)

            yield self.emitter.page_card(page_id, page.name, page.path)
            yield self.emitter.preview_update(page_id)
        except Exception as exc:  # noqa: BLE001 - surface generation errors
            yield self.emitter.task_failed(generate_key, f"{page.name} failed: {str(exc)}")
            plan_event = await self._mark_plan_task(
                session,
                generate_key,
                "failed",
                error=str(exc),
            )
            if plan_event:
                yield plan_event
            skip_event = await self._mark_plan_tasks(
                session,
                self._page_task_keys(page.id)[1:],
                "skipped",
                error="generation failed",
            )
            if skip_event:
                yield skip_event
            if page.id not in session.failed_pages:
                session.failed_pages.append(page.id)

    def _build_page_prompt(
        self,
        page: PageSpec,
        product_doc: object,
        session: BuildSession,
    ) -> str:
        overview = getattr(product_doc, "overview", "") or ""
        content_structure = getattr(product_doc, "content_structure", {}) or {}
        sections = (
            content_structure.get("sections", [])
            if isinstance(content_structure, dict)
            else []
        )
        page_sections = [s for s in sections if s.get("name") in page.sections] or sections
        design = getattr(product_doc, "design_requirements", {}) or {}

        prev_pages = [p.name for p in session.pages if p.id in session.completed_pages]
        nav_links = "\n".join([f"- {p.name}: {p.path}" for p in session.pages])

        return f"""
Generate a mobile-first HTML page.

## Page info
- Name: {page.name}
- Path: {page.path}
- Description: {page.description}
- Is home: {page.is_main}

## Project overview
{overview}

## Page sections
{_format_sections(page_sections)}

## Design requirements
- Style: {design.get("style", "modern")}
- Colors: {", ".join(design.get("colors", []) or []) or "neutral"}
- Typography: {design.get("typography", "sans-serif")}
- Mood: {design.get("mood", "professional")}

## Existing pages
{", ".join(prev_pages) if prev_pages else "This is the first page"}

## Site navigation
{nav_links}

## Technical requirements
- Use Tailwind CSS classes (no CDN script tags)
- Mobile-first responsive design
- Semantic HTML
- Do not use external images (use placeholders or SVG)
- Navigation includes links to all pages

Return a complete HTML document in ```html``` block. Optional JS in ```js``` block.
"""

    async def _save_page(
        self,
        project_id: str,
        page: PageSpec,
        html: str,
        js: str,
        order: int,
        product_doc: object,
    ) -> str:
        async with AsyncSessionLocal() as db:
            project_uuid = UUID(project_id)
            project = await db.get(Project, project_uuid)
            if not project:
                raise ValueError("Project not found")
            branch_id = project.active_branch_id
            page_row = await _find_page(db, project_uuid, branch_id, page.path, page.name)
            is_home = bool(page.is_main or page.path == "/")
            if is_home:
                await db.execute(
                    update(ProjectPage)
                    .where(
                        ProjectPage.project_id == project_uuid,
                        ProjectPage.branch_id == branch_id,
                    )
                    .values(is_home=False)
                )

            if page_row:
                page_row.name = page.name
                page_row.path = page.path
                page_row.slug = _slugify(page.name)
                page_row.is_home = is_home
                page_row.sort_order = order
                page_row.content = {"html": html, "js": js or ""}
            else:
                max_sort_result = await db.execute(
                    select(func.coalesce(func.max(ProjectPage.sort_order), -1))
                    .where(
                        ProjectPage.project_id == project_uuid,
                        ProjectPage.branch_id == branch_id,
                    )
                )
                max_sort = max_sort_result.scalar_one() or -1
                page_row = ProjectPage(
                    project_id=project_uuid,
                    branch_id=branch_id,
                    name=page.name,
                    slug=_slugify(page.name),
                    path=page.path,
                    is_home=is_home,
                    sort_order=max(max_sort + 1, order),
                    content={"html": html, "js": js or ""},
                    design_system=_design_system_from_doc(product_doc),
                )
                db.add(page_row)

            await db.commit()
            await db.refresh(page_row)
            return str(page_row.id)

    async def cancel_build(self, session_id: str) -> bool:
        session = self.sessions.get(session_id)
        if session:
            session.cancel()
            return True
        return False

    async def retry_page(
        self,
        session_id: str,
        page_id: str,
        product_doc: object,
    ) -> AsyncGenerator[BuildEvent, None]:
        session = self.sessions.get(session_id)
        if not session:
            yield self.emitter.task_failed("retry", "Build session not found")
            return

        if session.build_plan_id and not session.task_mapping:
            try:
                plan_uuid = UUID(session.build_plan_id)
                async with AsyncSessionLocal() as db:
                    plan = await db.get(DbBuildPlan, plan_uuid)
                    if plan:
                        session.task_mapping = self._build_task_mapping(plan, session.pages)
            except ValueError:
                pass

        if session.build_plan_id:
            plan_snapshot = await self._set_plan_status(session.build_plan_id, BuildStatus.RUNNING)
            if plan_snapshot:
                yield BuildEvent(type=BuildEventType.PLAN_UPDATE, plan_data=plan_snapshot)

        page = next((p for p in session.pages if p.id == page_id), None)
        if not page:
            yield self.emitter.task_failed("retry", "Page not found")
            return

        current_retry = session.retry_counts.get(page_id, 0) + 1
        session.retry_counts[page_id] = current_retry
        if current_retry > self.max_page_retries:
            yield self.emitter.task_failed(
                f"page-{page_id}",
                f"Retry limit reached ({self.max_page_retries})",
            )
            return

        if page_id in session.failed_pages:
            session.failed_pages.remove(page_id)

        async for event in self._generate_page(session, page, product_doc, 0):
            yield event

        if not session.failed_pages:
            project_events = await self._complete_project_tasks(session)
            for event in project_events:
                yield event
            if session.build_plan_id:
                plan_snapshot = await self._set_plan_status(
                    session.build_plan_id,
                    BuildStatus.COMPLETED,
                )
                if plan_snapshot:
                    yield BuildEvent(type=BuildEventType.PLAN_UPDATE, plan_data=plan_snapshot)
            if not session.failed_pages and not session.final_checks_failed:
                version_events = await self._emit_success_version(session)
                for event in version_events:
                    yield event
                return

        if session.failed_pages or session.final_checks_failed:
            await self._record_failed_version_attempt(session)
            if session.build_plan_id:
                plan_snapshot = await self._set_plan_status(
                    session.build_plan_id,
                    BuildStatus.FAILED,
                )
                if plan_snapshot:
                    yield BuildEvent(type=BuildEventType.PLAN_UPDATE, plan_data=plan_snapshot)


def _format_sections(sections: List[dict]) -> str:
    if not sections:
        return "- No sections provided"
    return "\n".join(
        f"- {s.get('name', 'Section')}: {s.get('description', '')} (priority: {s.get('priority', 'medium')})"
        for s in sections
        if isinstance(s, dict)
    )


def _validate_cross_page_links(
    page_html: dict[str, str],
    pages: List[PageSpec],
) -> tuple[bool, List[str]]:
    errors: List[str] = []
    for page in pages:
        html = page_html.get(page.id, "")
        if not html:
            errors.append(f"missing HTML for {page.name}")
            continue
        for target in pages:
            target_path = target.path or ""
            if not target_path:
                continue
            pattern = rf'href=[\"\\\']{re.escape(target_path)}[\"\\\']'
            if not re.search(pattern, html):
                errors.append(f"{page.name} missing link to {target_path}")
    return (len(errors) == 0, errors)


def _build_project_link_error_detail(message: str) -> dict:
    page_name = ""
    target_path = ""
    if " missing link to " in message:
        page_name, target_path = message.split(" missing link to ", 1)
    page_name = page_name.strip()
    path = f"pages/{_slugify(page_name)}.html" if page_name else ""
    suggested_fix = (
        f"Add a link to {target_path} on {page_name}."
        if page_name and target_path
        else "Update navigation links between pages."
    )
    return {
        "ruleId": "resource-missing-link",
        "ruleCategory": "resource",
        "path": path,
        "line": None,
        "excerpt": "",
        "message": message,
        "suggestedFix": suggested_fix,
        "severity": "critical",
    }


def _build_failed_message(session: BuildSession, validation_errors: list[dict]) -> str:
    if session.failed_pages:
        return f"Failed pages: {', '.join(session.failed_pages)}"
    if session.final_checks_failed:
        return "Project validation failed"
    if validation_errors:
        return f"{len(validation_errors)} validation errors"
    return "Build failed"


async def _find_page(
    db: AsyncSession,
    project_id: UUID,
    branch_id: UUID,
    path: str,
    name: str,
) -> Optional[ProjectPage]:
    result = await db.execute(
        select(ProjectPage).where(
            ProjectPage.project_id == project_id,
            ProjectPage.branch_id == branch_id,
            ProjectPage.path == path,
        )
    )
    page_row = result.scalar_one_or_none()
    if page_row:
        return page_row

    if name:
        result = await db.execute(
            select(ProjectPage).where(
                ProjectPage.project_id == project_id,
                ProjectPage.branch_id == branch_id,
                ProjectPage.name == name,
            )
        )
        return result.scalar_one_or_none()
    return None


def _extract_html_js(text: str) -> tuple[str, str]:
    html = _extract_code_block(text, "html")
    js = _extract_code_block(text, "js") or _extract_code_block(text, "javascript")
    if not html:
        html = text.strip()
    return html, js or ""


def _extract_code_block(text: str, lang: str) -> str:
    pattern = rf"```{lang}\s*([\s\S]*?)```"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"^-+|-+$", "", value)
    return value or "page"


def _design_system_from_doc(product_doc: object) -> dict:
    design = getattr(product_doc, "design_requirements", None)
    if not isinstance(design, dict):
        return {}
    colors = design.get("colors") if isinstance(design.get("colors"), list) else []
    primary = colors[0] if colors else None
    return {
        "colors": {"primary": primary} if primary else {},
        "style": design.get("style"),
    }


_MULTI_ORCHESTRATOR: Optional[MultiTaskOrchestrator] = None


def get_multi_task_orchestrator() -> MultiTaskOrchestrator:
    global _MULTI_ORCHESTRATOR
    if _MULTI_ORCHESTRATOR is None:
        _MULTI_ORCHESTRATOR = MultiTaskOrchestrator()
    return _MULTI_ORCHESTRATOR
