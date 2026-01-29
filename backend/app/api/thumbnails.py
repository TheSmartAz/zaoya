"""Thumbnail queue and client upload endpoints."""

from __future__ import annotations

from typing import Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.db import Project as DbProject, ProjectPage, Page
from app.models.db.thumbnail_job import ThumbnailJob
from app.models.user import get_current_user
from app.services.thumbnail_queue import thumbnail_queue
from app.api.projects import _resolve_user_id

router = APIRouter(tags=["thumbnails"])


class ThumbnailGenerateRequest(BaseModel):
    page_id: Optional[str] = None
    type: Literal["thumbnail", "og_image"] = "thumbnail"
    data_url: Optional[str] = None


class ThumbnailRetryRequest(BaseModel):
    data_url: Optional[str] = None


def _serialize_job(job: ThumbnailJob) -> dict:
    return {
        "id": str(job.id),
        "project_id": str(job.project_id),
        "page_id": str(job.page_id),
        "type": job.type,
        "status": job.status,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
        "last_error": job.last_error,
        "image_url": job.image_url,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


async def _get_project_for_user(
    project_id: str,
    current_user: dict,
    db: AsyncSession,
) -> DbProject:
    try:
        project_uuid = UUID(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc

    user_id = await _resolve_user_id(current_user, db)
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


@router.post("/api/projects/{project_id}/thumbnails/generate")
async def generate_thumbnails(
    project_id: str,
    request: ThumbnailGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Queue thumbnail or OG image generation (optionally client-provided)."""
    project = await _get_project_for_user(project_id, current_user, db)

    if request.data_url:
        if not request.page_id:
            raise HTTPException(status_code=400, detail="page_id required for client upload")
        try:
            page_uuid = UUID(request.page_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid page_id") from exc
        if request.type == "thumbnail":
            page_result = await db.execute(
                select(ProjectPage).where(
                    ProjectPage.id == page_uuid,
                    ProjectPage.project_id == project.id,
                    ProjectPage.branch_id == project.active_branch_id,
                )
            )
            if not page_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Page not found")
        else:
            if not project.published_snapshot_id:
                raise HTTPException(status_code=400, detail="Project not published")
            page_result = await db.execute(
                select(Page).where(
                    Page.id == page_uuid,
                    Page.snapshot_id == project.published_snapshot_id,
                )
            )
            if not page_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Published page not found")
        job = await thumbnail_queue.store_client_image(
            db=db,
            project_id=project.id,
            page_id=page_uuid,
            job_type=request.type,
            data_url=request.data_url,
        )
        return {"job": _serialize_job(job)}

    jobs: list[ThumbnailJob] = []
    if request.type == "thumbnail":
        if not project.active_branch_id:
            raise HTTPException(status_code=400, detail="Active branch not set")
        if request.page_id:
            try:
                page_uuid = UUID(request.page_id)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid page_id") from exc
            page_result = await db.execute(
                select(ProjectPage).where(
                    ProjectPage.id == page_uuid,
                    ProjectPage.project_id == project.id,
                    ProjectPage.branch_id == project.active_branch_id,
                )
            )
            page = page_result.scalar_one_or_none()
            if not page:
                raise HTTPException(status_code=404, detail="Page not found")
            jobs.append(
                await thumbnail_queue.enqueue_thumbnail(db, project.id, page.id)
            )
        else:
            pages_result = await db.execute(
                select(ProjectPage).where(
                    ProjectPage.project_id == project.id,
                    ProjectPage.branch_id == project.active_branch_id,
                )
            )
            pages = list(pages_result.scalars().all())
            if not pages:
                raise HTTPException(status_code=404, detail="No pages found")
            for page in pages:
                jobs.append(
                    await thumbnail_queue.enqueue_thumbnail(db, project.id, page.id)
                )
    else:
        if not project.published_snapshot_id:
            raise HTTPException(status_code=400, detail="Project not published")
        if request.page_id:
            try:
                page_uuid = UUID(request.page_id)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid page_id") from exc
            page_result = await db.execute(
                select(Page).where(
                    Page.id == page_uuid,
                    Page.snapshot_id == project.published_snapshot_id,
                )
            )
            page = page_result.scalar_one_or_none()
            if not page:
                raise HTTPException(status_code=404, detail="Published page not found")
            jobs.append(
                await thumbnail_queue.enqueue_og_image(db, project.id, page.id)
            )
        else:
            pages_result = await db.execute(
                select(Page).where(Page.snapshot_id == project.published_snapshot_id)
            )
            pages = list(pages_result.scalars().all())
            if not pages:
                raise HTTPException(status_code=404, detail="No published pages found")
            for page in pages:
                jobs.append(
                    await thumbnail_queue.enqueue_og_image(db, project.id, page.id)
                )

    return {"jobs": [_serialize_job(job) for job in jobs]}


@router.post("/api/projects/{project_id}/thumbnails/{thumbnail_id}/retry")
async def retry_thumbnail_job(
    project_id: str,
    thumbnail_id: str,
    request: ThumbnailRetryRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retry a failed thumbnail/OG image job."""
    project = await _get_project_for_user(project_id, current_user, db)

    try:
        job_uuid = UUID(thumbnail_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid thumbnail_id") from exc

    job = await db.get(ThumbnailJob, job_uuid)
    if not job or job.project_id != project.id:
        raise HTTPException(status_code=404, detail="Thumbnail job not found")

    if request.data_url:
        stored = await thumbnail_queue.store_client_image(
            db=db,
            project_id=project.id,
            page_id=job.page_id,
            job_type=job.type,
            data_url=request.data_url,
        )
        return {"job": _serialize_job(stored)}

    if job.type == "thumbnail":
        new_job = await thumbnail_queue.enqueue_thumbnail(db, project.id, job.page_id)
    else:
        new_job = await thumbnail_queue.enqueue_og_image(db, project.id, job.page_id)

    return {"job": _serialize_job(new_job)}


@router.get("/api/thumbnails/queue/status")
async def thumbnail_queue_status(
    project_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Return summary counts for thumbnail queue."""
    filters = []
    if project_id:
        try:
            filters.append(ThumbnailJob.project_id == UUID(project_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid project_id") from exc

    base_query = select(
        ThumbnailJob.type,
        ThumbnailJob.status,
        func.count().label("count"),
    )
    if filters:
        base_query = base_query.where(and_(*filters))
    base_query = base_query.group_by(ThumbnailJob.type, ThumbnailJob.status)

    result = await db.execute(base_query)
    rows = result.all()

    summary: dict[str, dict[str, int]] = {}
    for row in rows:
        summary.setdefault(row.type, {})[row.status] = row.count

    return {"by_type": summary}
