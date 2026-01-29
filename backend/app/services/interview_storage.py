"""Interview state storage backed by the database with optional memory fallback."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.interview_state import InterviewState as InterviewStateRow
from app.models.schemas.interview import InterviewState
from app.services.interview_orchestrator import create_initial_state


class InterviewStorage:
    """DB persistence for interview state."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_interview(self, project_id: str, user_id: UUID) -> InterviewState:
        project_uuid = UUID(project_id)
        result = await self.db.execute(
            select(InterviewStateRow).where(
                InterviewStateRow.project_id == project_uuid,
                InterviewStateRow.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            state = create_initial_state()
            state.project_id = project_id
            await self._create_row(state, project_uuid, user_id)
            return state
        state = InterviewState.model_validate(row.state or {})
        if not state.project_id:
            state.project_id = project_id
        return state

    async def save(self, state: InterviewState, user_id: UUID) -> None:
        if not state.project_id:
            raise ValueError("InterviewState.project_id is required")
        project_uuid = UUID(state.project_id)
        result = await self.db.execute(
            select(InterviewStateRow).where(
                InterviewStateRow.project_id == project_uuid,
                InterviewStateRow.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            await self._create_row(state, project_uuid, user_id)
            return
        row.state = state.model_dump(mode="json")
        row.status = state.status
        row.updated_at = datetime.utcnow()
        await self.db.commit()

    async def _create_row(self, state: InterviewState, project_uuid: UUID, user_id: UUID) -> None:
        row = InterviewStateRow(
            project_id=project_uuid,
            user_id=user_id,
            status=state.status,
            state=state.model_dump(mode="json"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(row)
        await self.db.commit()


class MemoryInterviewStorage:
    """Simple in-memory storage for interview states."""

    def __init__(self) -> None:
        self._states: Dict[str, InterviewState] = {}

    async def get_interview(self, project_id: str, user_id: Optional[UUID] = None) -> InterviewState:
        state = self._states.get(project_id)
        if state is None:
            state = create_initial_state()
            state.project_id = project_id
            self._states[project_id] = state
        return state

    async def save(self, state: InterviewState, user_id: Optional[UUID] = None) -> None:
        if state.project_id:
            self._states[state.project_id] = state


_memory_storage = MemoryInterviewStorage()


def get_interview_storage(db: Optional[AsyncSession]) -> tuple[object, bool]:
    """Return (storage, uses_db) based on environment configuration."""
    if os.getenv("ZAOYA_INTERVIEW_STORAGE") == "memory":
        return _memory_storage, False
    if db is None:
        raise RuntimeError("Database session required for interview storage")
    return InterviewStorage(db), True
