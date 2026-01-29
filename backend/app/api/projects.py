"""Project API endpoints for CRUD and publishing."""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import secrets
import string

from ..config import settings
from ..models.user import get_current_user
from ..services.validator import process_generation, extract_body_content
from app.services.template_renderer import build_inline_styles, strip_script_tags
from .versions import get_current_version_data, get_version_by_id
from app.db import get_db
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import Project as DbProject, ProjectPage, User as DbUser, Branch, ProductDoc
from app.models.db.thumbnail_job import ThumbnailJob
from app.services.build_runtime.planner import PageSpec
from app.services.build_runtime.multi_task_orchestrator import get_multi_task_orchestrator, BuildSession

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage (replace with database in production)
_projects_storage: Dict[str, dict] = {}

# Published versions storage
_published_pages: Dict[str, dict] = {}


# ============ Page Schemas ============

class PageCreate(BaseModel):
    """Schema for creating a new page."""
    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(default="/", max_length=255)
    is_home: bool = False


class PageUpdate(BaseModel):
    """Schema for updating a page."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    path: Optional[str] = Field(None, max_length=255)
    is_home: Optional[bool] = None
    sort_order: Optional[int] = None
    content: Optional[dict] = None
    design_system: Optional[dict] = None


class PageResponse(BaseModel):
    """Schema for page response."""
    id: UUID
    project_id: UUID
    name: str
    slug: Optional[str]
    path: str
    is_home: bool
    content: dict
    design_system: dict
    thumbnail_url: Optional[str] = None
    thumbnail_job_id: Optional[UUID] = None
    thumbnail_status: Optional[str] = None
    thumbnail_error: Optional[str] = None
    thumbnail_updated_at: Optional[datetime] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReorderPagesRequest(BaseModel):
    page_ids: List[UUID]


def get_user_projects(user_id: str) -> List[dict]:
    """Get all projects for a user."""
    return [p for p in _projects_storage.values() if p.get('userId') == user_id]


def get_project(project_id: str, user_id: str) -> Optional[dict]:
    """Get a project by ID for a user."""
    project = _projects_storage.get(project_id)
    if project and project.get('userId') == user_id:
        return project
    return None


def generate_public_id(length: int = 8) -> str:
    """Generate a URL-safe, memorable ID."""
    # Use alphanumeric without confusing chars
    alphabet = string.ascii_lowercase + string.digits
    # Remove confusing characters
    alphabet = alphabet.replace('0', '').replace('o', '').replace('l', '').replace('1', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def _resolve_user_id(current_user: dict, db: AsyncSession) -> UUID:
    """Resolve the current user to a UUID from the database."""
    try:
        return UUID(current_user["id"])
    except (KeyError, ValueError):
        if current_user.get("provider") == "dev" and current_user.get("email"):
            result = await db.execute(select(DbUser).where(DbUser.email == current_user["email"]))
            user = result.scalar_one_or_none()
            if user:
                return user.id

            user = DbUser(
                email=current_user["email"],
                name=current_user.get("name"),
                provider="dev",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user.id
        raise HTTPException(status_code=401, detail="Invalid user")


def _project_public_url(public_id: str | None) -> str | None:
    if not public_id:
        return None
    base_url = settings.pages_url.rstrip("/")
    return f"{base_url}/p/{public_id}"


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\n" f"data: {json.dumps(data, ensure_ascii=True)}\n\n"


def _normalize_path(path: str) -> str:
    value = (path or "/").strip()
    if not value.startswith("/"):
        value = f"/{value}"
    return value or "/"


def _build_page_specs(pages: List[ProjectPage], product_doc: ProductDoc) -> List[PageSpec]:
    plan_lookup: Dict[str, dict] = {}
    if isinstance(product_doc.page_plan, dict):
        for page in product_doc.page_plan.get("pages", []):
            if isinstance(page, dict):
                key = str(page.get("id") or page.get("name") or page.get("path") or "").strip()
                if key:
                    plan_lookup[key] = page

    specs: List[PageSpec] = []
    for page in pages:
        path = _normalize_path(page.path or "/")
        plan_page = (
            plan_lookup.get(str(page.id))
            or plan_lookup.get(page.name)
            or plan_lookup.get(path)
            or {}
        )
        sections = plan_page.get("sections") if isinstance(plan_page, dict) else []
        if not isinstance(sections, list):
            sections = []
        specs.append(
            PageSpec(
                id=str(page.id),
                name=page.name,
                path=path,
                description=str(plan_page.get("description", "")).strip()
                if isinstance(plan_page, dict)
                else "",
                is_main=page.is_home,
                sections=[str(s).strip() for s in sections if str(s).strip()],
            )
        )

    if specs and not any(p.is_main for p in specs):
        specs[0].is_main = True
        specs[0].path = "/"

    return specs


def _path_from_name(name: str) -> str:
    slug = "-".join(name.lower().split())
    return f"/{slug or 'page'}"


def _serialize_project(project: DbProject, viewer_id: UUID | None = None) -> dict:
    is_owner = viewer_id is not None and project.owner_id == viewer_id
    return {
        "id": str(project.id),
        "name": project.name,
        "owner_id": str(project.owner_id) if project.owner_id else None,
        "template_id": project.template_id,
        "template_inputs": project.template_inputs or {},
        "render_templates": project.render_templates or {},
        "status": project.status,
        "public_id": project.public_id,
        "active_branch_id": str(project.active_branch_id) if project.active_branch_id else None,
        "published_url": _project_public_url(project.public_id),
        "notification_email": project.notification_email,
        "notification_enabled": bool(project.notification_enabled),
        "published_at": project.published_at.isoformat() if project.published_at else None,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        "can_view_code": is_owner,
    }


def _sync_project_cache(
    project: DbProject,
    current_user: dict,
    *,
    published_url: str | None = None,
) -> None:
    """Keep legacy in-memory cache in sync for modules that still read it."""
    _projects_storage[str(project.id)] = {
        "id": str(project.id),
        "userId": current_user.get("id"),
        "name": project.name,
        "templateId": project.template_id,
        "templateInputs": project.template_inputs or {},
        "status": project.status,
        "draftVersionId": _projects_storage.get(str(project.id), {}).get("draftVersionId"),
        "publishedVersionId": _projects_storage.get(str(project.id), {}).get("publishedVersionId"),
        "publicId": project.public_id,
        "activeBranchId": str(project.active_branch_id) if project.active_branch_id else None,
        "publishedAt": project.published_at.isoformat() if project.published_at else None,
        "publishedUrl": published_url or _project_public_url(project.public_id),
        "notification_email": project.notification_email,
        "notification_enabled": bool(project.notification_enabled),
        "createdAt": project.created_at.isoformat() if project.created_at else None,
        "updatedAt": project.updated_at.isoformat() if project.updated_at else None,
    }


async def _get_project_or_404(
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


async def _get_page_or_404(
    page_id: str,
    current_user: dict,
    db: AsyncSession,
) -> ProjectPage:
    try:
        page_uuid = UUID(page_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Page not found") from exc

    user_id = await _resolve_user_id(current_user, db)
    result = await db.execute(
        select(ProjectPage)
        .join(DbProject, DbProject.id == ProjectPage.project_id)
        .where(
            ProjectPage.id == page_uuid,
            DbProject.user_id == user_id,
            ProjectPage.branch_id == DbProject.active_branch_id,
        )
    )
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


# ============ Page Endpoints ============

@router.get("/projects/{project_id}/pages", response_model=list[PageResponse])
async def list_project_pages(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pages in a project."""
    project = await _get_project_or_404(project_id, current_user, db)
    result = await db.execute(
        select(ProjectPage)
        .where(
            ProjectPage.project_id == project.id,
            ProjectPage.branch_id == project.active_branch_id,
        )
        .order_by(ProjectPage.sort_order)
    )
    pages = result.scalars().all()
    if not pages:
        return []

    page_ids = [page.id for page in pages]
    jobs_result = await db.execute(
        select(ThumbnailJob)
        .where(
            ThumbnailJob.project_id == project.id,
            ThumbnailJob.type == "thumbnail",
            ThumbnailJob.page_id.in_(page_ids),
        )
        .order_by(ThumbnailJob.page_id.asc(), ThumbnailJob.updated_at.desc())
    )
    jobs = jobs_result.scalars().all()
    job_map: dict[UUID, ThumbnailJob] = {}
    for job in jobs:
        if job.page_id not in job_map:
            job_map[job.page_id] = job

    payload = []
    for page in pages:
        job = job_map.get(page.id)
        payload.append(
            {
                "id": page.id,
                "project_id": page.project_id,
                "name": page.name,
                "slug": page.slug,
                "path": page.path,
                "is_home": page.is_home,
                "content": page.content,
                "design_system": page.design_system,
                "thumbnail_url": page.thumbnail_url,
                "thumbnail_job_id": job.id if job else None,
                "thumbnail_status": job.status if job else ("done" if page.thumbnail_url else None),
                "thumbnail_error": job.last_error if job else None,
                "thumbnail_updated_at": job.updated_at if job else None,
                "sort_order": page.sort_order,
                "created_at": page.created_at,
                "updated_at": page.updated_at,
            }
        )

    return payload


@router.post("/projects/{project_id}/pages", response_model=PageResponse)
async def create_project_page(
    project_id: str,
    page_data: PageCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new page in a project."""
    project = await _get_project_or_404(project_id, current_user, db)

    if page_data.is_home:
        await db.execute(
            update(ProjectPage)
            .where(
                ProjectPage.project_id == project.id,
                ProjectPage.branch_id == project.active_branch_id,
            )
            .values(is_home=False)
        )

    existing_home = await db.execute(
        select(ProjectPage.id).where(
            ProjectPage.project_id == project.id,
            ProjectPage.branch_id == project.active_branch_id,
            ProjectPage.is_home.is_(True),
        )
    )
    is_home = page_data.is_home or existing_home.scalar_one_or_none() is None

    next_sort = await db.execute(
        select(func.coalesce(func.max(ProjectPage.sort_order), -1) + 1).where(
            ProjectPage.project_id == project.id,
            ProjectPage.branch_id == project.active_branch_id,
        )
    )
    sort_order = next_sort.scalar_one() or 0

    page = ProjectPage(
        project_id=project.id,
        branch_id=project.active_branch_id,
        name=page_data.name,
        path=page_data.path,
        is_home=is_home,
        sort_order=sort_order,
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page


@router.patch("/projects/{project_id}/pages/reorder")
async def reorder_project_pages(
    project_id: str,
    request: ReorderPagesRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reorder pages in a project and set the first page as home."""
    project = await _get_project_or_404(project_id, current_user, db)

    result = await db.execute(
        select(ProjectPage).where(
            ProjectPage.project_id == project.id,
            ProjectPage.branch_id == project.active_branch_id,
        )
    )
    pages = result.scalars().all()
    if not pages:
        return {"status": "reordered", "page_ids": []}

    page_map = {page.id: page for page in pages}
    if set(request.page_ids) != set(page_map.keys()):
        raise HTTPException(status_code=400, detail="page_ids must include all pages")

    if not request.page_ids:
        raise HTTPException(status_code=400, detail="page_ids cannot be empty")

    # Update non-home pages first so '/' is free for the new home page.
    for order, page_id in enumerate(request.page_ids[1:], start=1):
        page = page_map.get(page_id)
        if not page:
            raise HTTPException(status_code=400, detail=f"Page {page_id} not found")
        page.sort_order = order
        page.is_home = False
        page.path = _path_from_name(page.name)

    home_id = request.page_ids[0]
    home_page = page_map.get(home_id)
    if not home_page:
        raise HTTPException(status_code=400, detail=f"Page {home_id} not found")
    home_page.sort_order = 0
    home_page.is_home = True
    home_page.path = "/"

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        logger.warning("Failed to reorder pages for project %s: %s", project_id, exc)
        raise HTTPException(status_code=400, detail="Failed to reorder pages") from exc

    return {"status": "reordered", "page_ids": [str(page_id) for page_id in request.page_ids]}


@router.patch("/projects/pages/{page_id}", response_model=PageResponse)
async def update_project_page(
    page_id: str,
    page_data: PageUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a project page."""
    page = await _get_page_or_404(page_id, current_user, db)
    should_version = page_data.content is not None or page_data.design_system is not None
    if page_data.is_home is True:
        project = await _get_project_or_404(str(page.project_id), current_user, db)
        await db.execute(
            update(ProjectPage)
            .where(
                ProjectPage.project_id == page.project_id,
                ProjectPage.branch_id == project.active_branch_id,
                ProjectPage.id != page.id,
            )
            .values(is_home=False)
        )

    if page_data.name is not None:
        page.name = page_data.name
    if page_data.path is not None:
        page.path = page_data.path
    if page_data.is_home is not None:
        page.is_home = page_data.is_home
    if page_data.sort_order is not None:
        page.sort_order = page_data.sort_order
    if page_data.content is not None:
        page.content = page_data.content
    if page_data.design_system is not None:
        page.design_system = page_data.design_system

    page.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(page)

    if should_version:
        try:
            from app.services.version_service import VersionService

            user_id = await _resolve_user_id(current_user, db)
            service = VersionService(db)
            await service.create_version_from_project(
                project_id=page.project_id,
                user_id=user_id,
                description=f"Updated {page.name}",
                tasks_completed=[f"Updated {page.name}"],
                validation_status="passed",
            )
        except Exception:
            pass
    return page


@router.delete("/projects/pages/{page_id}")
async def delete_project_page(
    page_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project page."""
    page = await _get_page_or_404(page_id, current_user, db)

    if page.is_home:
        raise HTTPException(status_code=400, detail="Cannot delete the home page")

    count_result = await db.execute(
        select(func.count()).where(
            ProjectPage.project_id == page.project_id,
            ProjectPage.branch_id == page.branch_id,
        )
    )
    if (count_result.scalar_one() or 0) <= 1:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the only page in a project",
        )

    await db.delete(page)
    await db.commit()
    return {"success": True}


@router.post("/projects")
async def create_project(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    requested_id = request.get("id")
    project_uuid: UUID | None = None
    if requested_id:
        try:
            project_uuid = UUID(requested_id)
        except ValueError:
            project_uuid = None

    if project_uuid is None:
        project_uuid = uuid4()
    else:
        existing = await db.execute(select(DbProject.id).where(DbProject.id == project_uuid))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Project ID already exists")

    user_id = await _resolve_user_id(current_user, db)

    db_project = DbProject(
        id=project_uuid,
        user_id=user_id,
        owner_id=user_id,
        name=request.get("name") or "Untitled",
        template_id=request.get("template_id"),
        template_inputs=request.get("template_inputs", {}),
        render_templates=request.get("render_templates") or {
            "preview": "preview_template_v1",
            "publish": "publish_template_v1",
        },
        status="draft",
    )
    db.add(db_project)
    await db.flush()
    branch = Branch(
        id=uuid4(),
        project_id=project_uuid,
        name="main",
        label="Main",
        is_default=True,
    )
    db.add(branch)
    db_project.active_branch_id = branch.id
    await db.commit()
    await db.refresh(db_project)
    _sync_project_cache(db_project, current_user)
    return _serialize_project(db_project, viewer_id=user_id)


@router.get("/projects")
async def list_projects(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for the current user."""
    user_id = await _resolve_user_id(current_user, db)
    result = await db.execute(
        select(DbProject).where(DbProject.user_id == user_id).order_by(DbProject.updated_at.desc())
    )
    projects = result.scalars().all()
    return [_serialize_project(project, viewer_id=user_id) for project in projects]


@router.get("/projects/{project_id}")
async def get_project_details(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project details."""
    project = await _get_project_or_404(project_id, current_user, db)
    user_id = await _resolve_user_id(current_user, db)
    return _serialize_project(project, viewer_id=user_id)


@router.patch("/projects/{project_id}")
async def update_project(
    project_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update project settings (currently notification settings)."""
    project = await _get_project_or_404(project_id, current_user, db)

    if "notification_email" in request:
        email = request.get("notification_email")
        project.notification_email = email or None

    if "notification_enabled" in request:
        project.notification_enabled = bool(request.get("notification_enabled"))

    if project.notification_enabled and not project.notification_email:
        project.notification_enabled = False

    project.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(project)
    _sync_project_cache(project, current_user)
    user_id = await _resolve_user_id(current_user, db)
    return _serialize_project(project, viewer_id=user_id)


@router.post("/projects/{project_id}/publish")
async def publish_project(
    project_id: str,
    _request: Optional[dict] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish a project."""
    project = await _get_project_or_404(project_id, current_user, db)

    project_id_str = str(project.id)
    draft_version_id = _projects_storage.get(project_id_str, {}).get("draftVersionId")
    version = get_version_by_id(project_id, draft_version_id) if draft_version_id else None
    if not version:
        version = get_current_version_data(project_id)
    if not version:
        raise HTTPException(status_code=400, detail="No draft to publish")

    html = version.html
    js = version.js

    is_valid, sanitized_html, sanitized_js, errors = process_generation(html, js)
    if not is_valid:
        raise HTTPException(status_code=422, detail={"errors": errors})

    # Generate public ID if first publish
    if not project.public_id:
        project.public_id = generate_public_id()

    # Store the published page (immutable snapshot)
    body_html = strip_script_tags(extract_body_content(sanitized_html))
    inline_css = build_inline_styles(body_html)

    _published_pages[project.public_id] = {
        "projectId": project_id_str,
        "html": sanitized_html,
        "js": sanitized_js or None,
        "inline_css": inline_css,
        "metadata": {
            "title": project.name,
            "publicId": project.public_id,
            "publishedAt": datetime.utcnow().isoformat(),
        }
    }

    # Update project
    project.status = "published"
    project.published_at = datetime.utcnow()
    project.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(project)

    # Generate the URL (published pages host)
    published_url = _project_public_url(project.public_id)
    cached = _projects_storage.get(project_id_str, {})
    cached["publishedVersionId"] = version.id
    _projects_storage[project_id_str] = cached
    _sync_project_cache(project, current_user, published_url=published_url)

    return {
        "publicId": project.public_id,
        "publishedAt": project.published_at.isoformat() if project.published_at else None,
        "url": published_url,
    }


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project."""
    project = await _get_project_or_404(project_id, current_user, db)

    if project.public_id:
        _published_pages.pop(project.public_id, None)

    await db.delete(project)
    await db.commit()
    _projects_storage.pop(str(project.id), None)
    return {"deleted": True}


@router.post("/projects/{project_id}/pages/{page_id}/retry")
async def retry_project_page(
    project_id: str,
    page_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retry generation for a single project page (SSE)."""
    try:
        project_uuid = UUID(project_id)
        page_uuid = UUID(page_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid project or page ID") from exc

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

    if not project.active_branch_id:
        raise HTTPException(status_code=400, detail="Active branch not set")

    page_result = await db.execute(
        select(ProjectPage).where(
            ProjectPage.id == page_uuid,
            ProjectPage.project_id == project.id,
            ProjectPage.branch_id == project.active_branch_id,
        )
    )
    target_page = page_result.scalar_one_or_none()
    if not target_page:
        raise HTTPException(status_code=404, detail="Page not found")

    doc_result = await db.execute(
        select(ProductDoc).where(ProductDoc.project_id == project.id)
    )
    product_doc = doc_result.scalar_one_or_none()
    if not product_doc:
        raise HTTPException(status_code=400, detail="ProductDoc required")

    pages_result = await db.execute(
        select(ProjectPage)
        .where(
            ProjectPage.project_id == project.id,
            ProjectPage.branch_id == project.active_branch_id,
        )
        .order_by(ProjectPage.sort_order)
    )
    pages = list(pages_result.scalars().all())
    if not pages:
        raise HTTPException(status_code=404, detail="No pages found")

    page_specs = _build_page_specs(pages, product_doc)

    orchestrator = get_multi_task_orchestrator()
    session_id = str(uuid4())
    session = BuildSession(
        id=session_id,
        project_id=str(project.id),
        user_id=str(user_id),
        pages=page_specs,
    )
    session.page_html = {
        str(p.id): (p.content or {}).get("html") or "" for p in pages if p.content
    }
    orchestrator.sessions[session_id] = session

    async def event_generator():
        try:
            async for event in orchestrator.retry_page(session_id, str(page_uuid), product_doc):
                payload = event.to_sse_event()
                if not payload:
                    continue
                data = payload.get("data", {})
                if isinstance(data, dict):
                    data["session_id"] = session_id
                    data["project_id"] = str(project.id)
                yield _format_sse(payload.get("event", "message"), data)

            session_state = orchestrator.sessions.get(session_id)
            if session_state:
                failed = session_state.failed_pages or session_state.final_checks_failed
                status = "failed" if failed else "done"
                title = (
                    "Retry completed with errors"
                    if failed
                    else "Retry complete"
                )
                yield _format_sse(
                    "task",
                    {
                        "id": f"build-{session_id}",
                        "type": "build_complete",
                        "title": title,
                        "status": status,
                        "session_id": session_id,
                        "project_id": str(project.id),
                    },
                )
        except Exception as exc:  # noqa: BLE001
            yield _format_sse("error", {"message": str(exc)})
        finally:
            orchestrator.sessions.pop(session_id, None)
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ============ Export/Import Endpoints ============

class ProjectExportData(BaseModel):
    """Schema for project export data."""
    project: dict
    pages: list[dict]


class ProjectImportRequest(BaseModel):
    """Schema for project import request."""
    data: ProjectExportData


@router.get("/projects/{project_id}/export")
async def export_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export project as JSON file."""
    project = await _get_project_or_404(project_id, current_user, db)
    from app.services.export_service import export_project_to_json

    export_data = await export_project_to_json(db, project.id)

    from fastapi.responses import StreamingResponse
    import json
    from io import BytesIO

    content = json.dumps(export_data, indent=2, ensure_ascii=False)
    buffer = BytesIO(content.encode("utf-8"))

    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="zaoya-project-{project.id}.json"'
        },
    )


@router.post("/projects/import")
async def import_project(
    request: ProjectImportRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import project from JSON data."""
    import_data = request.data
    user_id = await _resolve_user_id(current_user, db)

    project_payload = import_data.project or {}
    project = DbProject(
        user_id=user_id,
        owner_id=user_id,
        name=project_payload.get("name", "Imported Project"),
        template_id=project_payload.get("template_id"),
        template_inputs=project_payload.get("template_inputs", {}),
        render_templates=project_payload.get("render_templates") or {
            "preview": "preview_template_v1",
            "publish": "publish_template_v1",
        },
        notification_email=project_payload.get("notification_email"),
        notification_enabled=project_payload.get("notification_enabled", False),
        status="draft",
    )
    db.add(project)
    await db.flush()

    branch = Branch(
        id=uuid4(),
        project_id=project.id,
        name="main",
        label="Main",
        is_default=True,
    )
    db.add(branch)
    await db.flush()
    project.active_branch_id = branch.id

    pages_payload = import_data.pages or []
    has_home = any(page.get("is_home") for page in pages_payload)

    for index, page_data in enumerate(pages_payload):
        is_home = page_data.get("is_home", False) or (index == 0 and not has_home)
        page = ProjectPage(
            project_id=project.id,
            branch_id=branch.id,
            name=page_data.get("name", f"Page {index + 1}"),
            slug=page_data.get("slug"),
            path=page_data.get("path", "/"),
            is_home=is_home,
            content=page_data.get("content", {}),
            design_system=page_data.get("design_system", {}),
            sort_order=page_data.get("sort_order", index),
        )
        db.add(page)

    await db.commit()
    await db.refresh(project)
    _sync_project_cache(project, current_user)

    return {
        "id": str(project.id),
        "name": project.name,
        "message": "Project imported successfully",
    }
