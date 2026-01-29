"""ProductDoc API endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.db import ProductDoc, Project as DbProject
from app.models.user import get_current_user_db
from app.services.product_doc_service import ProductDocService
from app.services.intent_detector import ProductDocEditIntent

router = APIRouter(prefix="/api/projects/{project_id}/product-doc", tags=["product-doc"])


class ProductDocResponse(BaseModel):
    id: str
    project_id: str
    overview: str
    target_users: List[str]
    content_structure: dict
    design_requirements: Optional[dict]
    page_plan: dict
    technical_constraints: Optional[List[str]]
    interview_answers: List[dict]
    generation_count: int
    created_at: str
    updated_at: str
    last_generated_at: Optional[str] = None


class ProductDocUpdateRequest(BaseModel):
    overview: Optional[str] = None
    target_users: Optional[List[str]] = None
    content_structure: Optional[dict] = None
    design_requirements: Optional[dict] = None
    page_plan: Optional[dict] = None
    technical_constraints: Optional[List[str]] = None


class ProductDocEditRequest(BaseModel):
    message: str


class ProductDocEditResponse(BaseModel):
    handled: bool
    doc: Optional[ProductDocResponse] = None
    error: Optional[str] = None


async def _get_project_or_404(
    project_id: str,
    user_id: UUID,
    db: AsyncSession,
) -> DbProject:
    try:
        project_uuid = UUID(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc

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


def _coerce_list(value: Optional[object]) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = re.split(r"[,，\n]", value)
        return [part.strip() for part in parts if part.strip()]
    return [str(value).strip()]


def _apply_edit(doc: ProductDoc, intent: dict) -> None:
    field = intent.get("field")
    action = intent.get("action")
    value = intent.get("value")

    if field == "overview":
        if value:
            doc.overview = str(value).strip()
        return

    if field == "target_users":
        users = _coerce_list(value)
        current = doc.target_users or []
        if action == "add":
            doc.target_users = list({*current, *users})
        elif action == "remove":
            doc.target_users = [item for item in current if item not in users]
        else:
            doc.target_users = users
        return

    if field == "technical_constraints":
        constraints = _coerce_list(value)
        current = doc.technical_constraints or []
        if action == "add":
            doc.technical_constraints = list({*current, *constraints})
        elif action == "remove":
            doc.technical_constraints = [item for item in current if item not in constraints]
        else:
            doc.technical_constraints = constraints
        return

    if field == "page_plan.pages":
        pages = doc.page_plan or {"pages": []}
        page_list = pages.get("pages") if isinstance(pages, dict) else []
        if not isinstance(page_list, list):
            page_list = []
        if action == "add":
            new_page = value if isinstance(value, dict) else {"name": str(value).strip() if value else "新页面"}
            page_list.append(
                {
                    "id": new_page.get("id") or f"page-{uuid4().hex[:8]}",
                    "name": new_page.get("name") or "新页面",
                    "path": new_page.get("path") or "/",
                    "description": new_page.get("description") or "",
                    "is_main": bool(new_page.get("is_main", False)),
                    "sections": _coerce_list(new_page.get("sections")),
                }
            )
            pages["pages"] = page_list
            doc.page_plan = pages
        elif action == "remove" and value:
            remove_keys = _coerce_list(value)
            page_list = [
                page
                for page in page_list
                if page.get("name") not in remove_keys and page.get("path") not in remove_keys
            ]
            pages["pages"] = page_list
            doc.page_plan = pages
        return

    if field == "content_structure.sections":
        structure = doc.content_structure or {"sections": []}
        section_list = structure.get("sections") if isinstance(structure, dict) else []
        if not isinstance(section_list, list):
            section_list = []
        if action == "add":
            new_section = value if isinstance(value, dict) else {"name": str(value).strip() if value else "新模块"}
            section_list.append(
                {
                    "name": new_section.get("name") or "新模块",
                    "description": new_section.get("description") or "",
                    "priority": new_section.get("priority") or "medium",
                    "content_hints": _coerce_list(new_section.get("content_hints")),
                }
            )
            structure["sections"] = section_list
            doc.content_structure = structure
        elif action == "remove" and value:
            remove_keys = _coerce_list(value)
            section_list = [
                section for section in section_list if section.get("name") not in remove_keys
            ]
            structure["sections"] = section_list
            doc.content_structure = structure
        return

    if isinstance(field, str) and field.startswith("design_requirements."):
        design = doc.design_requirements or {}
        key = field.split(".", 1)[1]
        if key == "colors":
            design[key] = _coerce_list(value)
        else:
            design[key] = str(value).strip() if value is not None else None
        doc.design_requirements = design


@router.get("", response_model=ProductDocResponse)
async def get_product_doc(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_db),
) -> ProductDocResponse:
    """Get project's ProductDoc."""
    project = await _get_project_or_404(project_id, current_user.id, db)
    result = await db.execute(
        select(ProductDoc).where(ProductDoc.project_id == project.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="ProductDoc not found")
    return ProductDocResponse(**doc.to_dict())


@router.patch("", response_model=ProductDocResponse)
async def update_product_doc(
    project_id: str,
    req: ProductDocUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_db),
) -> ProductDocResponse:
    """Update ProductDoc fields."""
    project = await _get_project_or_404(project_id, current_user.id, db)
    result = await db.execute(
        select(ProductDoc).where(ProductDoc.project_id == project.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="ProductDoc not found")

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doc, field, value)

    doc.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(doc)
    return ProductDocResponse(**doc.to_dict())


@router.post("/regenerate", response_model=ProductDocResponse)
async def regenerate_product_doc(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_db),
) -> ProductDocResponse:
    """Regenerate ProductDoc from interview answers."""
    project = await _get_project_or_404(project_id, current_user.id, db)
    result = await db.execute(
        select(ProductDoc).where(ProductDoc.project_id == project.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="ProductDoc not found")

    service = ProductDocService()
    payload = await service.generate_payload(
        interview_answers=doc.interview_answers or [],
        project_type=project.template_id or project.name,
    )
    service.apply_payload(doc, payload)
    doc.generation_count = (doc.generation_count or 0) + 1
    doc.last_generated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(doc)
    return ProductDocResponse(**doc.to_dict())


@router.post("/edit", response_model=ProductDocEditResponse)
async def edit_product_doc(
    project_id: str,
    req: ProductDocEditRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_db),
) -> ProductDocEditResponse:
    """Parse a chat edit request and apply it to ProductDoc."""
    project = await _get_project_or_404(project_id, current_user.id, db)
    result = await db.execute(
        select(ProductDoc).where(ProductDoc.project_id == project.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="ProductDoc not found")

    detector = ProductDocEditIntent()
    intent = await detector.detect(req.message)
    if not intent:
        return ProductDocEditResponse(handled=False)

    try:
        _apply_edit(doc, intent)
        doc.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(doc)
        return ProductDocEditResponse(handled=True, doc=ProductDocResponse(**doc.to_dict()))
    except Exception as exc:
        return ProductDocEditResponse(handled=True, error=str(exc))
