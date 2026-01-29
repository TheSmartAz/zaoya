"""File API endpoints for Code Tab (read-only)."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.db import Project
from app.models.user import get_current_user_db
from app.services.file_service import (
    FileRecord,
    build_file_catalog,
    enforce_text_limit,
    is_safe_virtual_path,
    normalize_scope,
)

router = APIRouter(prefix="/api/projects", tags=["files"])


class FileEntry(BaseModel):
    path: str
    source: str
    size: Optional[int] = None
    mime_type: Optional[str] = None
    language: Optional[str] = None


class FileListResponse(BaseModel):
    scope: str
    files: List[FileEntry]


class FileContentResponse(BaseModel):
    path: str
    source: str
    content: Optional[str] = None
    url: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    language: Optional[str] = None


async def _get_project_or_403(
    project_id: str,
    user_id: UUID,
    db: AsyncSession,
) -> Project:
    try:
        project_uuid = UUID(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc

    result = await db.execute(select(Project).where(Project.id == project_uuid))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view code")

    return project


def _to_entry(record: FileRecord) -> FileEntry:
    return FileEntry(
        path=record.path,
        source=record.source,
        size=record.size,
        mime_type=record.mime_type,
        language=record.language,
    )


@router.get("/{project_id}/files", response_model=FileListResponse)
async def list_project_files(
    project_id: str,
    scope: str = Query("draft", pattern="^(draft|snapshot|published)$"),
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """List project files for Code Tab (owner only)."""
    project = await _get_project_or_403(project_id, current_user.id, db)
    try:
        scope_value = normalize_scope(scope)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scope")
    catalog = await build_file_catalog(db, project, scope_value)
    return FileListResponse(
        scope=scope_value,
        files=[_to_entry(record) for record in catalog.files],
    )


@router.get("/{project_id}/files/content", response_model=FileContentResponse)
async def get_file_content(
    project_id: str,
    path: str = Query(..., min_length=1, max_length=500),
    scope: str = Query("draft", pattern="^(draft|snapshot|published)$"),
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """Get file contents for Code Tab (owner only)."""
    if not is_safe_virtual_path(path):
        raise HTTPException(status_code=400, detail="Invalid file path")

    project = await _get_project_or_403(project_id, current_user.id, db)
    try:
        scope_value = normalize_scope(scope)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scope")
    catalog = await build_file_catalog(db, project, scope_value)
    record = catalog.by_path.get(path)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    record = enforce_text_limit(record)
    return FileContentResponse(
        path=record.path,
        source=record.source,
        content=record.content if record.source != "assets" else None,
        url=record.url if record.source == "assets" else None,
        size=record.size,
        mime_type=record.mime_type,
        language=record.language,
    )
