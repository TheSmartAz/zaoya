"""Project export helpers."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Project, ProjectPage


async def export_project_to_json(db: AsyncSession, project_id: UUID) -> dict:
    """Export project and its pages to a JSON-serializable dict."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise ValueError("Project not found")

    pages_result = await db.execute(
        select(ProjectPage)
        .where(
            ProjectPage.project_id == project_id,
            ProjectPage.branch_id == project.active_branch_id,
        )
        .order_by(ProjectPage.sort_order)
    )
    pages = pages_result.scalars().all()

    return {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "project": {
            "name": project.name,
            "template_id": project.template_id,
            "template_inputs": project.template_inputs or {},
            "render_templates": project.render_templates or {},
            "notification_email": project.notification_email,
            "notification_enabled": bool(project.notification_enabled),
        },
        "pages": [
            {
                "name": page.name,
                "slug": page.slug,
                "path": page.path,
                "is_home": page.is_home,
                "content": page.content or {},
                "design_system": page.design_system or {},
                "thumbnail_url": page.thumbnail_url,
                "sort_order": page.sort_order,
            }
            for page in pages
        ],
    }
