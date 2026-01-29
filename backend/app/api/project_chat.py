"""Project chat API with intent detection."""

from __future__ import annotations

import json
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, List, Literal
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4

from app.db import get_db
from app.models.user import get_current_user, get_current_user_db
from app.models.schemas.interview import (
    InterviewAnswerPayload,
    InterviewTurnResponse,
    InterviewState,
    OrchestratorResponse,
)
from app.models.db import Project as DbProject, ProductDoc
from app.models.db import ChatMessage
from app.services.interview_orchestrator import (
    build_first_question_response,
    orchestrate_turn,
    process_first_message,
)
from app.services.interview_storage import get_interview_storage
from app.services.build_runtime import BuildOrchestrator, BuildStorage
from app.services.build_runtime.events import BuildEvent
from app.services.build_runtime.planner import MultiPageDetector, PageSpec
from app.services.build_runtime.multi_task_orchestrator import get_multi_task_orchestrator
from app.services.product_doc_service import ProductDocService
from app.models.schemas.interview import FinishAction
from app.services.build_runtime.models import BuildPhase


router = APIRouter(prefix="/api/projects/{project_id}", tags=["chat"])


class ProjectChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    content: Optional[str] = None
    model: Optional[str] = None
    action: Optional[Literal["start", "answer", "skip", "generate_now", "skip_all"]] = None
    answers: List[InterviewAnswerPayload] = Field(default_factory=list)
    user_message: Optional[str] = Field(default=None, alias="userMessage")
    template: Optional[Dict[str, str]] = None
    template_inputs: Dict[str, str] = Field(default_factory=dict, alias="templateInputs")
    language: Optional[str] = None
    auto_detect_language: bool = True


async def stream_interview_questions(
    state: InterviewState,
    orchestrator: Optional[OrchestratorResponse] = None,
) -> AsyncGenerator[str, None]:
    if orchestrator is None:
        orchestrator = await build_first_question_response(state)
    payload = InterviewTurnResponse(state=state, orchestrator=orchestrator).model_dump()
    yield f"data: {json.dumps(payload, ensure_ascii=True)}\n\n"
    yield "data: [DONE]\n\n"


def _format_sse(event: str, data: Dict) -> str:
    return f"event: {event}\n" f"data: {json.dumps(data, ensure_ascii=True)}\n\n"


def _build_interview_card(state: InterviewState) -> Dict:
    question_lookup: Dict[str, Dict[str, str]] = {}
    for group in state.question_plan:
        for question in group.questions:
            question_lookup[question.id] = {
                "text": question.text,
                "hint": group.topic_label,
            }

    questions = []
    for item in state.asked:
        lookup = question_lookup.get(item.question_id, {})
        questions.append(
            {
                "id": item.question_id,
                "question": item.text or lookup.get("text", ""),
                "hint": lookup.get("hint"),
            }
        )

    answers: Dict[str, str] = {}
    answered_count = 0
    skipped_count = 0
    for answer in state.answers:
        if answer.selected_options and "skip" in answer.selected_options:
            skipped_count += 1
            continue
        if answer.raw_text:
            answers[answer.question_id] = answer.raw_text
            answered_count += 1
        elif answer.selected_options:
            answers[answer.question_id] = ", ".join(answer.selected_options)
            answered_count += 1
        else:
            skipped_count += 1

    return {
        "questions": questions,
        "answers": answers,
        "stats": {
            "asked": len(questions),
            "answered": answered_count,
            "skipped": skipped_count,
        },
    }


def _build_interview_answers(state: InterviewState) -> List[Dict[str, str]]:
    question_lookup: Dict[str, str] = {}
    for item in state.asked:
        question_lookup[item.question_id] = item.text

    answers_payload: List[Dict[str, str]] = []
    for answer in state.answers:
        if answer.selected_options and "skip" in answer.selected_options:
            continue
        response_text = answer.raw_text or ", ".join(answer.selected_options or [])
        if not response_text:
            continue
        answered_at = (
            datetime.utcfromtimestamp(answer.answered_at).isoformat()
            if answer.answered_at
            else datetime.utcnow().isoformat()
        )
        answers_payload.append(
            {
                "question_id": answer.question_id,
                "question": question_lookup.get(answer.question_id, ""),
                "answer": response_text,
                "answered_at": answered_at,
            }
        )

    return answers_payload


def _build_version_description(action: str, message: str) -> str:
    text = (message or "").strip()
    if text:
        return text[:160]
    if action == "start":
        return "Started project"
    if action == "answer":
        return "Updated interview answers"
    if action == "skip":
        return "Skipped interview step"
    if action == "skip_all":
        return "Skipped interview"
    if action == "generate_now":
        return "Generated draft"
    return "Updated project"


async def _record_chat_message(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    *,
    role: str,
    action: str,
    content: str,
) -> ChatMessage:
    message = ChatMessage(
        id=uuid4(),
        project_id=project_id,
        user_id=user_id,
        role=role,
        action=action,
        content=content or None,
        created_at=datetime.utcnow(),
    )
    db.add(message)
    await db.flush()
    return message


async def stream_build_events(
    project_id: str,
    user_id: str,
    seed: Dict,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    queue: asyncio.Queue[BuildEvent] = asyncio.Queue()

    def _enqueue(event: BuildEvent) -> None:
        queue.put_nowait(event)

    orchestrator = BuildOrchestrator(
        storage=BuildStorage(db),
        event_sink=_enqueue,
    )

    state = await orchestrator.start(
        project_id=project_id,
        user_id=user_id,
        brief=seed.get("brief", {}),
        build_plan=seed.get("build_plan"),
        product_doc=seed.get("product_doc"),
    )
    build_id = state.build_id

    yield _format_sse(
        "task",
        {
            "id": f"build-{build_id}",
            "type": "task_started",
            "title": "Build started",
            "status": "running",
            "session_id": build_id,
            "project_id": project_id,
        },
    )

    while not state.is_terminal:
        state = await orchestrator.step(build_id)

        while not queue.empty():
            event = await queue.get()
            payload = event.to_sse_event()
            if not payload:
                continue
            data = payload.get("data", {})
            if isinstance(data, dict):
                data["session_id"] = build_id
                data["project_id"] = project_id
                if payload.get("event") == "task" and data.get("type") == "build_complete":
                    data.setdefault("id", f"build-{build_id}")
                    data.setdefault("status", "done")
            yield _format_sse(payload.get("event", "message"), data)

    while not queue.empty():
        event = await queue.get()
        payload = event.to_sse_event()
        if not payload:
            continue
        data = payload.get("data", {})
        if isinstance(data, dict):
            data["session_id"] = build_id
            data["project_id"] = project_id
        yield _format_sse(payload.get("event", "message"), data)

    if state.phase in {BuildPhase.ERROR, BuildPhase.ABORTED}:
        title = "Build failed" if state.phase == BuildPhase.ERROR else "Build aborted"
        yield _format_sse(
            "task",
            {
                "id": f"build-{build_id}",
                "type": "build_complete",
                "title": title,
                "status": "failed",
                "session_id": build_id,
                "project_id": project_id,
            },
        )


@router.post("/chat")
async def chat_message(
    project_id: str,
    message: ProjectChatRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat endpoint with intent detection."""
    storage, uses_db = get_interview_storage(db)
    current_user_db = None
    project: Optional[DbProject] = None
    if uses_db:
        current_user_db = await get_current_user_db(user, db)
        project_uuid: UUID
        try:
            project_uuid = UUID(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid project ID") from exc

        result = await db.execute(
            select(DbProject).where(
                DbProject.id == project_uuid,
                DbProject.user_id == current_user_db.id,
            )
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    state = await storage.get_interview(
        project_id,
        current_user_db.id if current_user_db else None,
    )

    payload_message = message.user_message or message.content or ""
    action = message.action or "answer"
    if state.status == "not_started":
        action = "start"

    if action == "start":
        state = await process_first_message(
            project_id=project_id,
            message=payload_message,
            template=message.template,
            template_inputs=message.template_inputs,
            language=message.language or "en",
            auto_detect_language=message.auto_detect_language,
        )
        orchestrator = await build_first_question_response(
            state,
            user_message=payload_message,
            preferred_model=message.model,
        )
    else:
        orchestrator = await orchestrate_turn(
            state=state,
            action=action,
            answers=message.answers,
            user_message=payload_message,
            preferred_model=message.model,
        )

    await storage.save(state, current_user_db.id if current_user_db else None)

    should_build = False
    seed: Dict[str, Optional[dict]] = {}
    version_description = _build_version_description(action, payload_message)
    if isinstance(orchestrator.next_action, FinishAction):
        build_plan = orchestrator.next_action.plan or state.build_plan
        product_doc = orchestrator.next_action.product_document or state.product_document
        brief = orchestrator.next_action.brief or state.brief
        if build_plan:
            should_build = True
            seed = {
                "brief": brief.model_dump(mode="json") if hasattr(brief, "model_dump") else brief,
                "build_plan": (
                    build_plan.model_dump(mode="json")
                    if hasattr(build_plan, "model_dump")
                    else build_plan
                ),
                "product_doc": (
                    product_doc.model_dump(mode="json")
                    if hasattr(product_doc, "model_dump")
                    else product_doc
                ),
            }

    async def event_generator():
        version_emitted = False
        chat_message_id: Optional[UUID] = None
        if uses_db and current_user_db and project:
            try:
                recorded = await _record_chat_message(
                    db,
                    project.id,
                    current_user_db.id,
                    role="user",
                    action=action or "",
                    content=payload_message or "",
                )
                chat_message_id = recorded.id
                await db.commit()
            except Exception:
                await db.rollback()

        async def build_version_card_event() -> Optional[str]:
            nonlocal version_emitted
            if version_emitted or not uses_db or not current_user_db or not project:
                return None
            version_emitted = True
            try:
                from app.services.version_service import VersionService

                service = VersionService(db)
                version = await service.create_version_from_project(
                    project_id=project.id,
                    user_id=current_user_db.id,
                    description=version_description,
                    validation_status="passed",
                    trigger_message_id=chat_message_id,
                )
                snapshot = await service.get_version_snapshot(
                    project.id,
                    current_user_db.id,
                    version.id,
                )
                pages = snapshot.get("pages", []) if isinstance(snapshot, dict) else []
                home_page = next(
                    (p for p in pages if isinstance(p, dict) and p.get("is_home")),
                    pages[0] if pages else None,
                )
                return _format_sse(
                    "card",
                    {
                        "type": "version",
                        "data": {
                            "id": str(version.id),
                            "created_at": version.created_at.isoformat(),
                            "change_summary": version.change_summary,
                            "validation_status": version.validation_status,
                            "is_pinned": version.is_pinned,
                            "branch_label": version.branch_label,
                            "page_id": home_page.get("id") if isinstance(home_page, dict) else None,
                            "page_name": home_page.get("name") if isinstance(home_page, dict) else None,
                            "page_path": home_page.get("path") if isinstance(home_page, dict) else None,
                        },
                    },
                )
            except Exception:
                return None

        try:
            payload = InterviewTurnResponse(state=state, orchestrator=orchestrator).model_dump()
            yield f"data: {json.dumps(payload, ensure_ascii=True)}\n\n"

            product_doc_row = None
            if isinstance(orchestrator.next_action, FinishAction) and uses_db and current_user_db and project:
                yield _format_sse(
                    "task",
                    {
                        "id": "product-doc-generation",
                        "type": "task_started",
                        "title": "正在生成项目需求文档...",
                        "status": "running",
                    },
                )
                try:
                    answers_payload = _build_interview_answers(state)
                    service = ProductDocService()
                    payload_doc = await service.generate_payload(
                        interview_answers=answers_payload,
                        project_type=state.brief.project_type or project.template_id or project.name,
                    )

                    existing = await db.execute(
                        select(ProductDoc).where(ProductDoc.project_id == project.id)
                    )
                    doc = existing.scalar_one_or_none()
                    if doc:
                        service.apply_payload(doc, payload_doc)
                        doc.interview_answers = answers_payload
                        doc.generation_count = (doc.generation_count or 0) + 1
                        doc.last_generated_at = datetime.utcnow()
                    else:
                        doc = service.build_product_doc(
                            project_id=project.id,
                            payload=payload_doc,
                            interview_answers=answers_payload,
                            generation_count=1,
                        )
                        db.add(doc)

                    await db.commit()
                    await db.refresh(doc)
                    product_doc_row = doc

                    yield _format_sse(
                        "task",
                        {
                            "id": "product-doc-generation",
                            "type": "task_done",
                            "title": "项目需求文档已生成",
                            "status": "done",
                        },
                    )
                    yield _format_sse(
                        "card",
                        {
                            "type": "product_doc_ready",
                            "data": {"project_id": project_id},
                        },
                    )
                except Exception as exc:
                    yield _format_sse(
                        "task",
                        {
                            "id": "product-doc-generation",
                            "type": "task_failed",
                            "title": "项目需求文档生成失败",
                            "status": "failed",
                            "error": str(exc),
                        },
                    )

            if should_build and product_doc_row:
                detector = MultiPageDetector()
                decision = await detector.detect(
                    product_doc=product_doc_row,
                    user_message=payload_message,
                    project_type=(state.brief.project_type or project.template_id or project.name),
                )
                if decision.is_multi_page:
                    page_specs = detector.get_page_specs(
                        decision=decision,
                        product_doc=product_doc_row,
                        project_type=(state.brief.project_type or project.template_id or project.name),
                    )
                    yield _format_sse(
                        "card",
                        {
                            "type": "build_plan",
                            "project_id": project_id,
                            "data": {
                                "pages": [
                                    {
                                        "id": p.id,
                                        "name": p.name,
                                        "path": p.path,
                                        "is_main": p.is_main,
                                    }
                                    for p in page_specs
                                ],
                                "estimated_tasks": len(page_specs) * 3,
                                "project_type": state.brief.project_type or project.template_id,
                                "reason": decision.reason,
                                "approval_required": True,
                            },
                        },
                    )
                    version_card = await build_version_card_event()
                    if version_card:
                        yield version_card
                    yield "data: [DONE]\n\n"
                    return

            if should_build:
                interview_card = _build_interview_card(state)
                if interview_card["questions"] or interview_card["answers"]:
                    yield _format_sse(
                        "card",
                        {
                            "type": "interview",
                            "data": interview_card,
                        },
                    )
                async for event in stream_build_events(
                    project_id=project_id,
                    user_id=str(current_user_db.id) if current_user_db else str(user.get("id", "")),
                    seed=seed,
                    db=db,
                ):
                    yield event

            version_card = await build_version_card_event()
            if version_card:
                yield version_card
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield _format_sse("error", {"message": str(exc)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _normalize_path(path: str) -> str:
    value = (path or "/").strip()
    if not value.startswith("/"):
        value = f"/{value}"
    return value or "/"


class BuildPlanPagePayload(BaseModel):
    id: str
    name: str
    path: str
    is_main: bool = False


class BuildStartRequest(BaseModel):
    pages: List[BuildPlanPagePayload]


@router.post("/build/start")
async def start_multi_page_build(
    project_id: str,
    req: BuildStartRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start multi-page build after user approves the plan."""
    current_user_db = await get_current_user_db(user, db)
    project_uuid: UUID
    try:
        project_uuid = UUID(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid project ID") from exc

    result = await db.execute(
        select(DbProject).where(
            DbProject.id == project_uuid,
            DbProject.user_id == current_user_db.id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    doc_result = await db.execute(
        select(ProductDoc).where(ProductDoc.project_id == project.id)
    )
    product_doc = doc_result.scalar_one_or_none()
    if not product_doc:
        raise HTTPException(status_code=400, detail="ProductDoc required")

    plan_lookup: Dict[str, dict] = {}
    if isinstance(product_doc.page_plan, dict):
        for page in product_doc.page_plan.get("pages", []):
            if isinstance(page, dict):
                key = str(page.get("id") or page.get("name") or page.get("path") or "").strip()
                if key:
                    plan_lookup[key] = page

    pages: List[PageSpec] = []
    for p in req.pages:
        path = _normalize_path(p.path)
        plan_page = (
            plan_lookup.get(p.id)
            or plan_lookup.get(p.name)
            or plan_lookup.get(path)
            or {}
        )
        sections = plan_page.get("sections") if isinstance(plan_page, dict) else []
        if not isinstance(sections, list):
            sections = []
        pages.append(
            PageSpec(
                id=p.id,
                name=p.name,
                path=path,
                description=str(plan_page.get("description", "")).strip()
                if isinstance(plan_page, dict)
                else "",
                is_main=p.is_main,
                sections=[str(s).strip() for s in sections if str(s).strip()],
            )
        )
    if pages and not any(p.is_main for p in pages):
        pages[0].is_main = True
        pages[0].path = "/"

    orchestrator = get_multi_task_orchestrator()
    build_id = await orchestrator.start_build(
        project_id=str(project.id),
        user_id=str(current_user_db.id),
        pages=pages,
        product_doc=product_doc,
    )

    return {"build_id": build_id, "pages": len(pages)}
