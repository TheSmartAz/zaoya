"""Snapshots API endpoints for version management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import get_current_user
from app.models.db import User
from app.services.snapshot_service import SnapshotService
from app.models.schemas import (
    SnapshotResponse,
    CreateSnapshotRequest,
)

router = APIRouter(prefix="/api/projects/{project_id}/snapshots", tags=["snapshots"])


@router.get("", response_model=list[SnapshotResponse])
async def list_snapshots(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all non-draft snapshots for a project."""
    from uuid import UUID

    service = SnapshotService(db)
    snapshots = await service.list_snapshots(UUID(project_id), current_user.id)
    return [
        SnapshotResponse(
            id=s.id,
            project_id=s.project_id,
            version_number=s.version_number,
            summary=s.summary,
            design_system=s.design_system or {},
            navigation=s.navigation or {},
            is_draft=s.is_draft,
            created_at=s.created_at,
        )
        for s in snapshots
    ]


@router.post("", response_model=SnapshotResponse, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    project_id: str,
    request: CreateSnapshotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create an immutable snapshot from the current draft."""
    from uuid import UUID

    service = SnapshotService(db)
    snapshot = await service.create_snapshot(UUID(project_id), current_user.id, request)
    return SnapshotResponse(
        id=snapshot.id,
        project_id=snapshot.project_id,
        version_number=snapshot.version_number,
        summary=snapshot.summary,
        design_system=snapshot.design_system or {},
        navigation=snapshot.navigation or {},
        is_draft=snapshot.is_draft,
        created_at=snapshot.created_at,
    )


@router.post("/{snapshot_id}/restore", response_model=SnapshotResponse)
async def restore_snapshot(
    project_id: str,
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restore a snapshot to become the new draft."""
    from uuid import UUID

    service = SnapshotService(db)
    draft = await service.restore_snapshot(UUID(project_id), current_user.id, UUID(snapshot_id))
    return SnapshotResponse(
        id=draft.id,
        project_id=draft.project_id,
        version_number=draft.version_number,
        summary=draft.summary,
        design_system=draft.design_system or {},
        navigation=draft.navigation or {},
        is_draft=draft.is_draft,
        created_at=draft.created_at,
    )
