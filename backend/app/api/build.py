"""Build API - Agentic build orchestration endpoints."""

from __future__ import annotations

from typing import Optional
import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import get_current_user
from app.models.db import Project, User
from app.models.db.build_plan import BuildPlan as DbBuildPlan
from app.services.build_runtime.models import BuildState, BuildPhase
from app.services.build_runtime.orchestrator import BuildOrchestrator
from app.services.build_runtime.multi_task_orchestrator import get_multi_task_orchestrator
from app.models.db import ProductDoc
from app.services.build_runtime.storage import BuildStorage
from app.services.build_runtime.events import BuildEvent

router = APIRouter(prefix="/api/build", tags=["build"])


class StartBuildRequest(BaseModel):
    project_id: str = Field(..., description="Project ID to build")
    seed: dict = Field(..., description="Build seed with brief, build_plan, product_doc")


class StepRequest(BaseModel):
    build_id: str = Field(..., description="Build ID to step")
    user_message: Optional[str] = Field(None, description="User feedback for iterating")
    mode: str = Field(
        default="auto",
        description="Step mode: auto | plan_only | implement_only | verify_only",
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
    token_usage: Optional[dict] = None
    agent_usage: Optional[list] = None
    last_agent_usage: Optional[dict] = None
    history: list


class BuildPlanResponse(BaseModel):
    id: str
    project_id: str
    created_at: str | None
    pages: list
    tasks: list
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    estimated_duration_ms: int | None
    actual_duration_ms: int | None
    started_at: str | None
    completed_at: str | None
    status: str


class CanPublishResponse(BaseModel):
    can_publish: bool
    reasons: list[str]


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\n" f"data: {json.dumps(data, ensure_ascii=True)}\n\n"


async def _resolve_user_id(current_user: dict, db: AsyncSession) -> UUID:
    """Resolve the current user to a UUID from the database."""
    try:
        return UUID(current_user["id"])
    except (KeyError, ValueError):
        if current_user.get("provider") == "dev" and current_user.get("email"):
            result = await db.execute(select(User).where(User.email == current_user["email"]))
            user = result.scalar_one_or_none()
            if user:
                return user.id
        raise HTTPException(status_code=401, detail="Invalid user")


async def _ensure_project_access(project_id: UUID, user_id: UUID, db: AsyncSession) -> None:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/start", response_model=BuildResponse)
async def start_build(
    req: StartBuildRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> BuildResponse:
    """
    Start a new build run from interview artifacts.

    Creates a new BuildState in 'planning' phase with the provided seed.
    """
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


@router.post("/step", response_model=BuildResponse)
async def step_build(
    req: StepRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> BuildResponse:
    """
    Advance build by one step.
    """
    orchestrator = BuildOrchestrator(storage=BuildStorage(db))

    try:
        state = await orchestrator.step(
            build_id=req.build_id,
            user_message=req.user_message,
            mode=req.mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to step build: {str(exc)}",
        )

    user_id = await _resolve_user_id(user, db)
    if state.user_id != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this build")

    return _state_to_response(state)


@router.get("/{build_id}", response_model=BuildResponse)
async def get_build(
    build_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> BuildResponse:
    """Get current build state."""
    storage = BuildStorage(db)

    try:
        state = await storage.get(build_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Build not found")

    if not state:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")

    user_id = await _resolve_user_id(user, db)
    if state.user_id != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this build")

    return _state_to_response(state)


@router.get("/{build_id}/stream")
async def stream_build(
    build_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Stream build progress events with SSE (resume on reconnect)."""
    multi_orchestrator = get_multi_task_orchestrator()
    if build_id in multi_orchestrator.sessions:
        async def event_generator():
            session = multi_orchestrator.sessions.get(build_id)
            if not session:
                yield _format_sse("error", {"message": "Build session not found"})
                return

            user_id = await _resolve_user_id(user, db)
            if session.user_id != str(user_id):
                yield _format_sse("error", {"message": "Not authorized to access this build"})
                return

            doc_result = await db.execute(
                select(ProductDoc).where(ProductDoc.project_id == UUID(session.project_id))
            )
            product_doc = doc_result.scalar_one_or_none()
            if not product_doc:
                yield _format_sse("error", {"message": "ProductDoc not found"})
                return

            async for event in multi_orchestrator.stream_progress(build_id, product_doc):
                payload = event.to_sse_event()
                if not payload:
                    continue
                data = payload.get("data", {})
                if isinstance(data, dict):
                    data["session_id"] = build_id
                    data["project_id"] = session.project_id
                    if payload.get("event") == "task" and data.get("type") == "build_complete":
                        data.setdefault("id", f"build-{build_id}")
                        data.setdefault("status", "done")
                yield _format_sse(payload.get("event", "message"), data)

            yield "data: [DONE]\n\n"

        from fastapi.responses import StreamingResponse

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    queue: asyncio.Queue[BuildEvent] = asyncio.Queue()

    def _enqueue(event: BuildEvent) -> None:
        queue.put_nowait(event)

    storage = BuildStorage(db)

    async def event_generator():
        try:
            state = await storage.get(build_id)
            if not state:
                yield _format_sse("error", {"message": "Build not found"})
                return

            user_id = await _resolve_user_id(user, db)
            if state.user_id != str(user_id):
                yield _format_sse("error", {"message": "Not authorized to access this build"})
                return

            orchestrator = BuildOrchestrator(storage=storage, event_sink=_enqueue)

            if state.is_terminal:
                yield _format_sse(
                    "task",
                    {
                        "id": f"build-{state.build_id}",
                        "type": "build_complete",
                        "title": "Build complete",
                        "status": "done",
                        "session_id": state.build_id,
                        "project_id": state.project_id,
                    },
                )
                yield "data: [DONE]\n\n"
                return

            while not state.is_terminal:
                state = await orchestrator.step(build_id)

                while not queue.empty():
                    event = await queue.get()
                    payload = event.to_sse_event()
                    if not payload:
                        continue
                    data = payload.get("data", {})
                    if isinstance(data, dict):
                        data["session_id"] = state.build_id
                        data["project_id"] = state.project_id
                        if payload.get("event") == "task" and data.get("type") == "build_complete":
                            data.setdefault("id", f"build-{state.build_id}")
                            data.setdefault("status", "done")
                    yield _format_sse(payload.get("event", "message"), data)

            if state.phase in {BuildPhase.ERROR, BuildPhase.ABORTED}:
                title = "Build failed" if state.phase == BuildPhase.ERROR else "Build aborted"
                yield _format_sse(
                    "task",
                    {
                        "id": f"build-{state.build_id}",
                        "type": "build_complete",
                        "title": title,
                        "status": "failed",
                        "session_id": state.build_id,
                        "project_id": state.project_id,
                    },
                )

            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield _format_sse("error", {"message": str(exc)})

    from fastapi.responses import StreamingResponse

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{build_id}/plan", response_model=BuildPlanResponse)
async def get_build_plan(
    build_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> BuildPlanResponse:
    """Get current build plan with task statuses."""
    try:
        plan_uuid = UUID(build_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid build ID") from exc

    plan = await db.get(DbBuildPlan, plan_uuid)
    if not plan:
        raise HTTPException(status_code=404, detail="Build plan not found")

    user_id = await _resolve_user_id(user, db)
    result = await db.execute(
        select(Project).where(Project.id == plan.project_id, Project.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized")

    return BuildPlanResponse(**plan.to_dict())


@router.post("/{build_id}/abort", response_model=BuildResponse)
async def abort_build(
    build_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> BuildResponse:
    """Abort a running build."""
    multi_orchestrator = get_multi_task_orchestrator()
    if build_id in multi_orchestrator.sessions:
        session = multi_orchestrator.sessions.get(build_id)
        if not session:
            raise HTTPException(status_code=404, detail="Build session not found")
        user_id = await _resolve_user_id(user, db)
        if session.user_id != str(user_id):
            raise HTTPException(status_code=403, detail="Not authorized to access this build")
        await multi_orchestrator.cancel_build(build_id)
        return BuildResponse(
            build_id=build_id,
            project_id=session.project_id,
            phase=BuildPhase.ABORTED.value,
            current_task_id=None,
            build_graph=None,
            last_patch=None,
            last_validation=None,
            last_checks=None,
            last_review=None,
            token_usage=None,
            agent_usage=None,
            last_agent_usage=None,
            history=[],
        )

    orchestrator = BuildOrchestrator(storage=BuildStorage(db))

    try:
        state = await orchestrator.abort(build_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    user_id = await _resolve_user_id(user, db)
    if state.user_id != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this build")

    return _state_to_response(state)


@router.get("/{build_id}/retry/{page_id}")
async def retry_multi_page(
    build_id: str,
    page_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Retry a failed page generation for multi-page builds (SSE)."""
    multi_orchestrator = get_multi_task_orchestrator()
    session = multi_orchestrator.sessions.get(build_id)
    if not session:
        raise HTTPException(status_code=404, detail="Build session not found")

    user_id = await _resolve_user_id(user, db)
    if session.user_id != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this build")

    doc_result = await db.execute(
        select(ProductDoc).where(ProductDoc.project_id == UUID(session.project_id))
    )
    product_doc = doc_result.scalar_one_or_none()
    if not product_doc:
        raise HTTPException(status_code=404, detail="ProductDoc not found")

    async def event_generator():
        async for event in multi_orchestrator.retry_page(build_id, page_id, product_doc):
            payload = event.to_sse_event()
            if not payload:
                continue
            data = payload.get("data", {})
            if isinstance(data, dict):
                data["session_id"] = build_id
                data["project_id"] = session.project_id
                if payload.get("event") == "task" and data.get("type") == "build_complete":
                    data.setdefault("id", f"build-{build_id}")
                    data.setdefault("status", "done")
            yield _format_sse(payload.get("event", "message"), data)

        if session.failed_pages:
            yield _format_sse(
                "task",
                {
                    "id": f"build-{build_id}",
                    "type": "build_complete",
                    "title": f"Build completed with {len(session.failed_pages)} failed page(s)",
                    "status": "failed",
                    "session_id": build_id,
                    "project_id": session.project_id,
                },
            )
        else:
            yield _format_sse(
                "task",
                {
                    "id": f"build-{build_id}",
                    "type": "build_complete",
                    "title": "Build complete",
                    "status": "done",
                    "session_id": build_id,
                    "project_id": session.project_id,
                },
            )
            multi_orchestrator.sessions.pop(build_id, None)

        yield "data: [DONE]\n\n"

    from fastapi.responses import StreamingResponse

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{build_id}/can-publish", response_model=CanPublishResponse)
async def can_publish(
    build_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> CanPublishResponse:
    """Check if build is ready for publish."""
    storage = BuildStorage(db)

    try:
        state = await storage.get(build_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Build not found")

    if not state:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")

    user_id = await _resolve_user_id(user, db)
    if state.user_id != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this build")

    can_publish = (
        state.phase.value == "ready"
        and state.last_validation is not None
        and state.last_validation.ok
        and state.last_checks is not None
        and state.last_checks.ok
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
        reasons=reasons if not can_publish else [],
    )


def _state_to_response(state: BuildState) -> BuildResponse:
    """Convert BuildState to API response."""
    return BuildResponse(
        build_id=state.build_id,
        project_id=state.project_id,
        phase=state.phase.value,
        current_task_id=state.current_task_id,
        build_graph=state.build_graph.model_dump(mode="json") if state.build_graph else None,
        last_patch=state.last_patch.model_dump(mode="json") if state.last_patch else None,
        last_validation=state.last_validation.model_dump(mode="json") if state.last_validation else None,
        last_checks=state.last_checks.model_dump(mode="json") if state.last_checks else None,
        last_review=state.last_review.model_dump(mode="json") if state.last_review else None,
        token_usage=state.total_token_usage().model_dump(mode="json"),
        agent_usage=[u.model_dump(mode="json") for u in state.agent_usage],
        last_agent_usage=state.last_agent_usage.model_dump(mode="json") if state.last_agent_usage else None,
        history=[h.model_dump(mode="json") for h in state.history],
    )
