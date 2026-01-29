"""Project branch management API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.db import Project as DbProject, Branch
from app.models.user import get_current_user_db
from app.models.schemas import BranchListResponse, BranchResponse

router = APIRouter(prefix="/api/projects/{project_id}/branches", tags=["branches"])


async def _get_project_or_404(
    project_id: str,
    user_id: UUID,
    db: AsyncSession,
) -> DbProject:
    try:
        project_uuid = UUID(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid project ID") from exc
    result = await db.execute(
        select(DbProject).where(
            DbProject.id == project_uuid,
            DbProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=BranchListResponse)
async def list_branches(
    project_id: str,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(project_id, current_user.id, db)
    result = await db.execute(
        select(Branch)
        .where(Branch.project_id == project.id)
        .order_by(Branch.created_at.asc())
    )
    branches = result.scalars().all()
    return BranchListResponse(
        branches=[BranchResponse.model_validate(branch) for branch in branches],
        active_branch_id=project.active_branch_id,
    )


@router.post("/{branch_id}/activate", response_model=BranchResponse)
async def activate_branch(
    project_id: str,
    branch_id: str,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(project_id, current_user.id, db)
    try:
        branch_uuid = UUID(branch_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid branch ID") from exc

    result = await db.execute(
        select(Branch).where(Branch.id == branch_uuid, Branch.project_id == project.id)
    )
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    project.active_branch_id = branch.id
    await db.commit()
    await db.refresh(branch)
    return BranchResponse.model_validate(branch)
