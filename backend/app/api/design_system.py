"""Design system endpoints for draft projects."""

from __future__ import annotations

import re
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.db import Page, User
from app.models.schemas import DesignSystem, DraftUpdate
from app.models.user import get_current_user_db
from app.services.draft_service import DraftService

router = APIRouter(prefix="/api/projects/{project_id}/design-system", tags=["design-system"])

PRESET_THEMES: Dict[str, Dict] = {
    "pink-princess": {
        "colors": {"primary": "#FF69B4", "secondary": "#FFC0CB", "accent": "#FF1493"},
        "animation_level": "moderate",
        "preset_theme": "pink-princess",
    },
    "blue-ocean": {
        "colors": {"primary": "#0077B6", "secondary": "#00B4D8", "accent": "#90E0EF"},
        "animation_level": "subtle",
        "preset_theme": "blue-ocean",
    },
    "forest-green": {
        "colors": {"primary": "#2D6A4F", "secondary": "#40916C", "accent": "#52B788"},
        "animation_level": "subtle",
        "preset_theme": "forest-green",
    },
    "sunset": {
        "colors": {"primary": "#F77F00", "secondary": "#FCBF49", "accent": "#FDE68A"},
        "animation_level": "energetic",
        "preset_theme": "sunset",
    },
    "minimal-black": {
        "colors": {"primary": "#1A1A1A", "secondary": "#4A4A4A", "accent": "#7A7A7A"},
        "animation_level": "none",
        "preset_theme": "minimal-black",
    },
}

_DESIGN_STYLE_RE = re.compile(
    r'<style[^>]*id=["\\\']zaoya-design-system["\\\'][^>]*>.*?</style>',
    re.IGNORECASE | re.DOTALL,
)


def _build_design_css(design_system: Dict) -> str:
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    spacing = design_system.get("spacing", "comfortable")
    border_radius = design_system.get("border_radius", "medium")
    animation_level = design_system.get("animation_level", "subtle")

    css_vars = []
    for key, value in colors.items():
        css_vars.append(f"--color-{key}: {value};")
    heading = typography.get("heading", {})
    body = typography.get("body", {})
    if heading:
        css_vars.append(f"--font-heading-family: {heading.get('family', 'Inter')};")
        css_vars.append(f"--font-heading-size: {heading.get('size', 'large')};")
        css_vars.append(f"--font-heading-weight: {heading.get('weight', 600)};")
        css_vars.append(f"--font-heading-line-height: {heading.get('line_height', 1.4)};")
    if body:
        css_vars.append(f"--font-body-family: {body.get('family', 'Inter')};")
        css_vars.append(f"--font-body-size: {body.get('size', 'medium')};")
        css_vars.append(f"--font-body-weight: {body.get('weight', 400)};")
        css_vars.append(f"--font-body-line-height: {body.get('line_height', 1.6)};")

    spacing_map = {
        "compact": "12px",
        "comfortable": "16px",
        "spacious": "20px",
    }
    radius_map = {
        "none": "0px",
        "small": "4px",
        "medium": "8px",
        "large": "16px",
        "full": "9999px",
    }
    animation_map = {
        "none": "0ms",
        "subtle": "150ms",
        "moderate": "250ms",
        "energetic": "400ms",
    }

    css_vars.append(f"--spacing-base: {spacing_map.get(spacing, '16px')};")
    css_vars.append(f"--radius-base: {radius_map.get(border_radius, '8px')};")
    css_vars.append(f"--animation-duration: {animation_map.get(animation_level, '150ms')};")

    return f":root {{\n  {'\\n  '.join(css_vars)}\n}}"


def _apply_design_system_html(html: str, css: str) -> str:
    style_block = f'<style id="zaoya-design-system">{css}</style>'

    if _DESIGN_STYLE_RE.search(html):
        return _DESIGN_STYLE_RE.sub(style_block, html)

    head_close_idx = html.lower().find("</head>")
    if head_close_idx != -1:
        return f"{html[:head_close_idx]}{style_block}\n{html[head_close_idx:]}"

    return f"{style_block}\n{html}"


@router.get("", response_model=DesignSystem)
async def get_design_system(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db),
):
    """Get the current draft's design system."""
    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    service = DraftService(db)
    draft = await service.get_or_create_draft(pid, current_user.id)
    return DesignSystem(**(draft.design_system or {}))


@router.put("", response_model=DesignSystem)
async def update_design_system(
    project_id: str,
    design_system: DesignSystem,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db),
):
    """Replace the current draft's design system."""
    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    service = DraftService(db)
    await service.update_draft(pid, current_user.id, DraftUpdate(design_system=design_system))
    return design_system


@router.post("/apply-preset", response_model=DesignSystem)
async def apply_design_preset(
    project_id: str,
    payload: Dict[str, str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db),
):
    """Apply a preset theme to the current draft design system."""
    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    preset_key = payload.get("preset")
    if not preset_key or preset_key not in PRESET_THEMES:
        raise HTTPException(status_code=400, detail="Unknown preset")

    service = DraftService(db)
    draft = await service.get_or_create_draft(pid, current_user.id)
    current = draft.design_system or {}

    update = PRESET_THEMES[preset_key]
    merged = {**current, **update}
    await service.update_draft(pid, current_user.id, DraftUpdate(design_system=DesignSystem.model_validate(merged)))
    return DesignSystem.model_validate(merged)


@router.post("/apply")
async def apply_design_system(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db),
):
    """Apply the draft design system across all draft pages."""
    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    service = DraftService(db)
    draft = await service.get_or_create_draft(pid, current_user.id)
    design_system = draft.design_system or {}
    css = _build_design_css(design_system)

    pages_result = await db.execute(
        select(Page).where(Page.snapshot_id == draft.id)
    )
    pages = list(pages_result.scalars().all())

    for page in pages:
        page.html = _apply_design_system_html(page.html or "", css)

    await db.commit()

    return {"updated": len(pages)}
