"""Build storage for persistence of build artifacts."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.build_run import BuildRun

from .models import BuildState


class BuildStorage:
    """DB persistence for build artifacts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, state: BuildState) -> BuildState:
        """Create new build run."""
        payload = self._state_to_payload(state)
        run = BuildRun(**payload)
        self.db.add(run)
        await self.db.commit()
        return state

    async def get(self, build_id: str) -> Optional[BuildState]:
        """Get build by ID."""
        build_uuid = UUID(build_id)
        result = await self.db.execute(
            select(BuildRun).where(BuildRun.build_id == build_uuid)
        )
        run = result.scalar_one_or_none()
        if not run:
            return None
        return self._row_to_state(run)

    async def save(self, state: BuildState) -> None:
        """Update existing build."""
        state.updated_at = datetime.utcnow()
        build_uuid = UUID(state.build_id)

        result = await self.db.execute(
            select(BuildRun).where(BuildRun.build_id == build_uuid)
        )
        run = result.scalar_one_or_none()
        if not run:
            raise ValueError(f"Build {state.build_id} not found")

        payload = self._state_to_payload(state)
        for key, value in payload.items():
            setattr(run, key, value)

        await self.db.commit()

    async def list_by_project(self, project_id: str) -> List[BuildState]:
        """List all builds for a project."""
        project_uuid = UUID(project_id)
        result = await self.db.execute(
            select(BuildRun)
            .where(BuildRun.project_id == project_uuid)
            .order_by(desc(BuildRun.created_at))
        )
        runs = result.scalars().all()
        return [self._row_to_state(run) for run in runs]

    async def get_latest_by_project(self, project_id: str) -> Optional[BuildState]:
        """Get most recent build for a project."""
        project_uuid = UUID(project_id)
        result = await self.db.execute(
            select(BuildRun)
            .where(BuildRun.project_id == project_uuid)
            .order_by(desc(BuildRun.created_at))
            .limit(1)
        )
        run = result.scalar_one_or_none()
        if not run:
            return None
        return self._row_to_state(run)

    def _state_to_payload(self, state: BuildState) -> dict:
        data = state.model_dump(mode="json")
        build_uuid = UUID(data["build_id"])

        return {
            "id": build_uuid,
            "build_id": build_uuid,
            "project_id": UUID(data["project_id"]),
            "user_id": UUID(data["user_id"]),
            "phase": data["phase"],
            "current_task_id": data.get("current_task_id"),
            "brief": data.get("brief") or {},
            "build_plan": data.get("build_plan"),
            "product_doc": data.get("product_doc"),
            "build_graph": data.get("build_graph"),
            "patch_sets": data.get("patch_sets") or [],
            "last_patch": data.get("last_patch"),
            "validation_reports": data.get("validation_reports") or [],
            "last_validation": data.get("last_validation"),
            "check_reports": data.get("check_reports") or [],
            "last_checks": data.get("last_checks"),
            "review_reports": data.get("review_reports") or [],
            "last_review": data.get("last_review"),
            "agent_usage": data.get("agent_usage") or [],
            "last_agent_usage": data.get("last_agent_usage"),
            "history": data.get("history") or [],
            "created_at": state.created_at,
            "updated_at": state.updated_at,
            "completed_at": state.completed_at,
        }

    def _row_to_state(self, run: BuildRun) -> BuildState:
        return BuildState(
            build_id=str(run.build_id),
            project_id=str(run.project_id),
            user_id=str(run.user_id),
            phase=run.phase,
            current_task_id=run.current_task_id,
            brief=run.brief or {},
            build_plan=run.build_plan,
            product_doc=run.product_doc,
            build_graph=run.build_graph,
            patch_sets=run.patch_sets or [],
            last_patch=run.last_patch,
            validation_reports=run.validation_reports or [],
            last_validation=run.last_validation,
            check_reports=run.check_reports or [],
            last_checks=run.last_checks,
            review_reports=run.review_reports or [],
            last_review=run.last_review,
            agent_usage=run.agent_usage or [],
            last_agent_usage=run.last_agent_usage,
            history=run.history or [],
            created_at=run.created_at,
            updated_at=run.updated_at,
            completed_at=run.completed_at,
        )
