from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Literal, Optional


class BuildEventType(Enum):
    TASK_STARTED = "task_started"
    TASK_DONE = "task_done"
    TASK_FAILED = "task_failed"
    AGENT_THINKING = "agent_thinking"
    TOOL_CALL = "tool_call"
    CARD = "card"
    PREVIEW_UPDATE = "preview_update"
    PLAN_UPDATE = "plan_update"
    BUILD_COMPLETE = "build_complete"


@dataclass
class BuildEvent:
    type: BuildEventType
    task_id: Optional[str] = None
    title: Optional[str] = None
    status: Optional[Literal["running", "done", "failed"]] = None
    card_type: Optional[str] = None
    card_data: Optional[Dict[str, Any]] = None
    plan_data: Optional[Dict[str, Any]] = None
    page_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

    def to_sse_event(self) -> Dict[str, Any]:
        if self.type in {
            BuildEventType.TASK_STARTED,
            BuildEventType.TASK_DONE,
            BuildEventType.TASK_FAILED,
            BuildEventType.AGENT_THINKING,
            BuildEventType.TOOL_CALL,
        }:
            return {
                "event": "task",
                "data": {
                    "id": self.task_id,
                    "type": self.type.value,
                    "title": self.title,
                    "status": self.status or "running",
                },
            }
        if self.type == BuildEventType.CARD:
            return {
                "event": "card",
                "data": {
                    "type": self.card_type,
                    "data": self.card_data,
                },
            }
        if self.type == BuildEventType.PLAN_UPDATE:
            return {
                "event": "plan_update",
                "data": self.plan_data or {},
            }
        if self.type == BuildEventType.PREVIEW_UPDATE:
            return {"event": "preview_update", "data": {"page_id": self.page_id}}
        if self.type == BuildEventType.BUILD_COMPLETE:
            return {
                "event": "task",
                "data": {
                    "type": "build_complete",
                    "title": self.message or "构建完成",
                },
            }
        return {}


class BuildEventEmitter:
    def task_started(self, task_id: str, title: str) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.TASK_STARTED,
            task_id=task_id,
            title=title,
            status="running",
        )

    def task_done(self, task_id: str, title: str) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.TASK_DONE,
            task_id=task_id,
            title=title,
            status="done",
        )

    def task_failed(self, task_id: str, title: str, error: str | None = None) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.TASK_FAILED,
            task_id=task_id,
            title=title,
            status="failed",
            error=error,
        )

    def page_card(self, page_id: str, name: str, path: str) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.CARD,
            card_type="page",
            card_data={
                "id": page_id,
                "name": name,
                "path": path,
            },
        )

    def build_plan_card(
        self,
        pages: list[dict],
        tasks: list[dict],
        estimated_tasks: int,
        features: list[str] | None = None,
        design_system: dict | None = None,
        estimated_complexity: str | None = None,
    ) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.CARD,
            card_type="build_plan",
            card_data={
                "pages": pages,
                "tasks": tasks,
                "estimated_tasks": estimated_tasks,
                "features": features or [],
                "design_system": design_system or {},
                "estimated_complexity": estimated_complexity,
            },
        )

    def validation_card(
        self,
        errors: list[dict],
        suggestions: list[str],
        page_id: str | None = None,
        page_name: str | None = None,
        page_path: str | None = None,
        retry_count: int | None = None,
    ) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.CARD,
            card_type="validation",
            card_data={
                "errors": errors,
                "suggestions": suggestions,
                "page_id": page_id,
                "page_name": page_name,
                "page_path": page_path,
                "retry_count": retry_count,
            },
        )

    def version_card(self, version: dict) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.CARD,
            card_type="version",
            card_data=version,
        )

    def preview_update(self, page_id: str) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.PREVIEW_UPDATE,
            page_id=page_id,
        )

    def agent_thinking(self, task_id: str, title: str) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.AGENT_THINKING,
            task_id=task_id,
            title=title,
            status="running",
        )

    def tool_call(self, task_id: str, title: str) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.TOOL_CALL,
            task_id=task_id,
            title=title,
            status="running",
        )

    def build_complete(self, message: str | None = None) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.BUILD_COMPLETE,
            message=message,
        )
