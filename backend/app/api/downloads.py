"""Project download endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db import get_db
from app.models.db import Project, Snapshot, Page
from app.models.user import get_current_user_db
from app.services.download_service import DownloadOptions, build_zip_package, generate_html


router = APIRouter(prefix="/api/projects/{project_id}", tags=["download"])


@router.get("/download")
async def download_project(
    project_id: str,
    format: str = "html",
    include_runtime: bool = True,
    include_comments: bool = False,
    include_metadata: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_db),
):
    """Download project output as HTML/ZIP/source."""
    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Project).where(Project.id == pid, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    draft_result = await db.execute(
        select(Snapshot).where(
            Snapshot.project_id == pid,
            Snapshot.is_draft == True,
        )
    )
    draft = draft_result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    pages_result = await db.execute(
        select(Page).where(Page.snapshot_id == draft.id).order_by(Page.display_order)
    )
    pages = list(pages_result.scalars().all())
    if not pages:
        raise HTTPException(status_code=400, detail="No pages to download")

    options = DownloadOptions(
        format=format,
        include_runtime=include_runtime,
        include_comments=include_comments,
        include_metadata=include_metadata,
    )

    if format == "html":
        home = next((p for p in pages if p.is_home), pages[0])
        html = generate_html(draft, home, options)
        safe_name = (project.slug or project.name or "zaoya").strip().replace(" ", "-")
        filename = f"{safe_name}.html"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=html, media_type="text/html", headers=headers)

    if format in {"zip", "source"}:
        include_source = format == "source"
        zip_bytes, filename = build_zip_package(draft, pages, options, include_source=include_source)
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=zip_bytes, media_type="application/zip", headers=headers)

    raise HTTPException(status_code=400, detail="Unsupported format")
