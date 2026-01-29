"""Published page serving API endpoints."""

import os
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlparse
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Response, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import get_current_user, get_current_user_db
from .projects import get_project
from .versions import get_current_version_data, get_version_by_id
from app.db import get_db
from app.models.db import Project as DbProject, ProjectPage, SimulationReport, Page
from app.services.csp import build_preview_csp, build_publish_csp, build_sim_csp
from app.services.template_renderer import (
    PREVIEW_TEMPLATE,
    build_inline_styles,
    render_preview_document,
    render_publish_document,
    resolve_template_name,
    strip_script_tags,
)
from app.services.validator import extract_body_content
from app.services.thumbnail_queue import thumbnail_queue

router = APIRouter()


def _normalize_sim_report(payload: Any) -> tuple[str, dict] | None:
    if isinstance(payload, dict):
        if "type" in payload and isinstance(payload.get("report"), dict):
            return str(payload.get("type") or "runtime"), payload["report"]
        if "csp-report" in payload and isinstance(payload["csp-report"], dict):
            return "csp", payload["csp-report"]
        if "report" in payload and isinstance(payload["report"], dict):
            return "csp", payload["report"]
        if "body" in payload and isinstance(payload["body"], dict):
            report_type = payload.get("type") or "csp"
            return str(report_type), payload["body"]
        if payload:
            return "runtime", payload
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict):
            body = first.get("body")
            if isinstance(body, dict):
                report_type = first.get("type") or "csp"
                return str(report_type), body
    return None

# In-memory storage (shared with projects.py)
# In production, this would be database queries
_published_pages = {}

# Import from projects module to access shared storage
try:
    from ..api.projects import _published_pages
except ImportError:
    _published_pages = {}


def _get_api_base() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8000")


def _origin_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return url


async def _resolve_project_id_from_report(report: dict, db: AsyncSession) -> UUID | None:
    doc_uri = report.get("document-uri") or report.get("documentURL") or report.get("document-url")
    if not doc_uri:
        return None
    parsed = urlparse(doc_uri)
    path = parsed.path or ""
    public_id = ""
    if path.startswith("/p/"):
        parts = path.split("/")
        if len(parts) > 2:
            public_id = parts[2]
    if not public_id:
        return None
    result = await db.execute(
        select(DbProject).where(DbProject.public_id == public_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        return None
    return project.id


def _build_sim_report_script(project_id: str) -> str:
    return f"""
(function() {{
  'use strict';
  const reportUrl = '/p-sim-report/{project_id}';
  const seen = new Set();

  function send(type, payload) {{
    try {{
      const body = JSON.stringify({{ type: type, report: payload }});
      const key = type + ':' + body;
      if (seen.has(key)) return;
      seen.add(key);
      if (seen.size > 50) {{
        seen.clear();
      }}
      if (navigator.sendBeacon) {{
        const blob = new Blob([body], {{ type: 'application/json' }});
        navigator.sendBeacon(reportUrl, blob);
        return;
      }}
      fetch(reportUrl, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: body,
        keepalive: true
      }}).catch(function(){{}});
    }} catch (err) {{
      // Ignore reporting failures
    }}
  }}

  window.addEventListener('error', function(event) {{
    try {{
      const target = event.target || event.srcElement;
      if (target && target !== window && (target.src || target.href)) {{
        send('resource', {{
          tag: target.tagName || 'unknown',
          url: target.src || target.href || '',
          page: location.pathname
        }});
        return;
      }}
      send('runtime', {{
        message: event.message || 'Runtime error',
        filename: event.filename || '',
        lineno: event.lineno || 0,
        colno: event.colno || 0,
        stack: event.error && event.error.stack ? event.error.stack : ''
      }});
    }} catch (err) {{
      // Ignore
    }}
  }}, true);

  window.addEventListener('unhandledrejection', function(event) {{
    try {{
      const reason = event.reason || {{}};
      send('runtime', {{
        message: reason.message || String(reason) || 'Unhandled rejection',
        stack: reason.stack || ''
      }});
    }} catch (err) {{
      // Ignore
    }}
  }});
}})();
"""


async def _get_project_for_owner(
    project_id: str,
    user_id: UUID,
    db: AsyncSession,
) -> DbProject:
    try:
        project_uuid = UUID(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc

    result = await db.execute(select(DbProject).where(DbProject.id == project_uuid))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return project


async def _get_project_page_for_sim(
    project_id: str,
    page_slug: Optional[str],
    user_id: UUID,
    db: AsyncSession,
) -> tuple[DbProject, ProjectPage]:
    project = await _get_project_for_owner(project_id, user_id, db)
    project_uuid = project.id

    page: ProjectPage | None = None
    if page_slug:
        page_result = await db.execute(
            select(ProjectPage).where(
                ProjectPage.project_id == project_uuid,
                ProjectPage.branch_id == project.active_branch_id,
                ProjectPage.slug == page_slug,
            )
        )
        page = page_result.scalar_one_or_none()

    if not page:
        page_result = await db.execute(
            select(ProjectPage)
            .where(
                ProjectPage.project_id == project_uuid,
                ProjectPage.branch_id == project.active_branch_id,
            )
            .order_by(ProjectPage.is_home.desc(), ProjectPage.sort_order)
        )
        page = page_result.scalars().first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return project, page


def _preview_styles(html_body: str) -> str:
    styles = build_inline_styles(html_body)
    if styles:
        return styles
    return '<script src="https://cdn.tailwindcss.com"></script>'


@router.get("/p-sim/{project_id}")
@router.get("/p-sim/{project_id}/{page_slug}")
async def serve_publish_simulation(
    project_id: str,
    page_slug: Optional[str] = None,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """Serve publish simulation page for preview (owner-only)."""
    project, page = await _get_project_page_for_sim(project_id, page_slug, current_user.id, db)

    content = page.content or {}
    html = content.get("html") or ""
    js = content.get("js") or ""

    html_body = strip_script_tags(extract_body_content(html))
    styles = build_inline_styles(html_body)
    page_slug_value = page.slug or "home"
    script_tag = (
        f'<script src="/p-sim/{project_id}/{page_slug_value}.js" defer></script>'
        if js.strip()
        else ""
    )
    report_script_tag = f'<script src="/p-sim/{project_id}/sim-report" defer></script>'
    combined_script_tag = f"{script_tag}{report_script_tag}"

    template_name = resolve_template_name(
        (project.render_templates or {}).get("preview"),
        PREVIEW_TEMPLATE,
    )

    html_doc = render_preview_document(
        body_html=html_body,
        title=f"{project.name} (Sim)",
        styles=styles,
        body_class="antialiased",
        page_script_tag=combined_script_tag,
        template_name=template_name,
    )

    api_base = _get_api_base()
    api_origin = _origin_from_url(api_base)

    report_uri = f"/p-sim-report/{project_id}"

    return HTMLResponse(
        content=html_doc,
        status_code=200,
        headers={
            "Content-Security-Policy": build_sim_csp(api_origin, report_uri=report_uri),
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        },
    )


@router.post("/p-sim-report/{project_id}")
async def collect_publish_simulation_report(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Collect CSP violation reports for publish simulation."""
    try:
        UUID(project_id)
    except ValueError:
        return Response(status_code=204)

    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=204)

    normalized = _normalize_sim_report(payload)
    if not normalized:
        return Response(status_code=204)

    report_type, report = normalized
    db.add(
        SimulationReport(
            id=uuid4(),
            project_id=UUID(project_id),
            report_type=report_type,
            report=report,
            user_agent=request.headers.get("user-agent", ""),
            created_at=datetime.utcnow(),
        )
    )
    await db.commit()
    return Response(status_code=204)


@router.get("/p-sim-report/{project_id}")
async def get_publish_simulation_report(
    project_id: str,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
    since_minutes: int = Query(30, ge=1, le=1440),
):
    """Return CSP violation reports for publish simulation (owner-only)."""
    await _get_project_for_owner(project_id, current_user.id, db)
    since = datetime.utcnow() - timedelta(minutes=since_minutes)
    result = await db.execute(
        select(SimulationReport)
        .where(
            SimulationReport.project_id == UUID(project_id),
            SimulationReport.created_at >= since,
        )
        .order_by(SimulationReport.created_at.desc())
    )
    rows = list(result.scalars().all())

    csp_violations = []
    resource_errors = []
    runtime_errors = []
    for row in rows:
        entry = {
            "received_at": row.created_at.isoformat() + "Z",
            "user_agent": row.user_agent or "",
            "report": row.report,
        }
        if row.report_type == "csp":
            csp_violations.append(entry)
        elif row.report_type == "resource":
            resource_errors.append(entry)
        else:
            runtime_errors.append(entry)

    status = "failed" if (csp_violations or resource_errors or runtime_errors) else "passed"
    return {
        "project_id": project_id,
        "status": status,
        "csp_violations": csp_violations,
        "resource_errors": resource_errors,
        "runtime_errors": runtime_errors,
        "count": len(rows),
        "since_minutes": since_minutes,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/api/csp-report")
async def collect_csp_report(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Compatibility endpoint for CSP report-uri."""
    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=204)

    normalized = _normalize_sim_report(payload)
    if not normalized:
        return Response(status_code=204)

    report_type, report = normalized
    if not isinstance(report, dict):
        return Response(status_code=204)

    project_id = await _resolve_project_id_from_report(report, db)
    if not project_id:
        return Response(status_code=204)

    db.add(
        SimulationReport(
            id=uuid4(),
            project_id=project_id,
            report_type=str(report_type),
            report=report,
            user_agent=request.headers.get("user-agent", ""),
            created_at=datetime.utcnow(),
        )
    )
    await db.commit()
    return Response(status_code=204)


@router.get("/p-sim/{project_id}/{page_slug}.js")
async def serve_publish_simulation_script(
    project_id: str,
    page_slug: str,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """Serve JS for publish simulation (owner-only)."""
    project, page = await _get_project_page_for_sim(project_id, page_slug, current_user.id, db)
    content = page.content or {}
    js = content.get("js") or ""
    if not js.strip():
        return Response(status_code=204)
    return Response(
        content=js,
        media_type="application/javascript",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/p-sim/{project_id}/sim-report")
async def serve_publish_simulation_report_script(
    project_id: str,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """Serve JS that reports runtime/resource errors for publish simulation."""
    await _get_project_for_owner(project_id, current_user.id, db)
    return Response(
        content=_build_sim_report_script(project_id),
        media_type="application/javascript",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/og-image/{project_id}/{page_id}")
async def serve_og_image(
    project_id: str,
    page_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Serve or generate Open Graph images for published pages."""
    try:
        project_uuid = UUID(project_id)
        page_uuid = UUID(page_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid project or page ID") from exc

    project = await db.get(DbProject, project_uuid)
    if not project or project.status != "published" or not project.published_snapshot_id:
        raise HTTPException(status_code=404, detail="Project not published")

    page_result = await db.execute(
        select(Page).where(
            Page.id == page_uuid,
            Page.snapshot_id == project.published_snapshot_id,
        )
    )
    page = page_result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    job = await thumbnail_queue.get_latest_job(db, project_uuid, page_uuid, "og_image")
    if job and job.status == "done" and job.image_url:
        return RedirectResponse(job.image_url, status_code=302)

    if job and job.status == "queued":
        await thumbnail_queue.bump_job_priority(db, project_uuid, page_uuid, "og_image")
        image_url = await thumbnail_queue.process_job_now(job.id)
        if image_url:
            return RedirectResponse(image_url, status_code=302)

    image_url = await thumbnail_queue.generate_og_image_now(project_uuid, page_uuid)
    if image_url:
        return RedirectResponse(image_url, status_code=302)

    if job and job.image_url:
        return RedirectResponse(job.image_url, status_code=302)

    raise HTTPException(status_code=404, detail="OG image unavailable")


@router.get("/p/{public_id}")
async def serve_published_page(public_id: str):
    """Serve a published page."""
    # Import here to avoid circular imports
    from ..api.projects import _published_pages as published_pages

    page_data = published_pages.get(public_id)

    if not page_data:
        raise HTTPException(status_code=404, detail="Page not found")

    api_base = _get_api_base()
    api_origin = _origin_from_url(api_base)

    raw_html = page_data['html']
    html_body = strip_script_tags(extract_body_content(raw_html))
    styles = page_data.get("inline_css") or build_inline_styles(html_body)
    script_tag = f'<script src="/p/{public_id}.js" defer></script>' if page_data.get('js') else ''
    metadata = page_data.get('metadata', {})
    title = metadata.get('title', 'Zaoya Page')
    description = metadata.get('description', 'Created with Zaoya - Describe it. See it. Share it.')
    og_image = metadata.get('ogImage', '')
    canonical = f"{_get_api_base().rstrip('/')}/p/{public_id}"
    og_url = canonical
    favicon_url = (
        metadata.get("favicon")
        or metadata.get("favicon_url")
        or metadata.get("faviconUrl")
        or f"{_get_api_base().rstrip('/')}/favicon.ico"
    )

    html = render_publish_document(
        body_html=html_body,
        title=title,
        description=description,
        og_image=og_image,
        og_url=og_url,
        canonical_url=canonical,
        public_id=public_id,
        api_base=api_base,
        styles=styles,
        body_class="antialiased",
        page_script_tag=script_tag,
        favicon_url=favicon_url,
        robots_content="index, follow",
    )

    return HTMLResponse(
        content=html,
        status_code=200,
        headers={
            "Content-Security-Policy": build_publish_csp(api_origin),
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        }
    )


@router.head("/p/{public_id}")
async def head_published_page(public_id: str):
    """HEAD request for published pages (for curl checks)."""
    from ..api.projects import _published_pages as published_pages

    page_data = published_pages.get(public_id)

    if not page_data:
        raise HTTPException(status_code=404, detail="Page not found")

    return Response(status_code=200)


@router.get("/p/{public_id}.js")
async def serve_published_script(public_id: str):
    """Serve the published page JS as a separate file."""
    from ..api.projects import _published_pages as published_pages

    page_data = published_pages.get(public_id)
    if not page_data:
        raise HTTPException(status_code=404, detail="Page not found")

    js_content = page_data.get("js")
    if not js_content:
        return Response(status_code=204)

    return Response(
        content=js_content,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.get("/draft/{project_id}")
async def serve_draft_page(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Serve a draft preview page (requires auth)."""
    project = get_project(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    draft_version_id = project.get("draftVersionId")
    version = get_version_by_id(project_id, draft_version_id) if draft_version_id else None
    if not version:
        version = get_current_version_data(project_id)
    if not version:
        raise HTTPException(status_code=404, detail="Draft not found")

    api_base = _get_api_base()
    api_origin = _origin_from_url(api_base)

    html_body = strip_script_tags(extract_body_content(version.html))
    styles = _preview_styles(html_body)
    script_tag = f'<script src="/draft/{project_id}.js" defer></script>' if version.js else ''
    html = render_preview_document(
        body_html=html_body,
        title=f"{project.get('name', 'Zaoya Draft')} (Draft)",
        styles=styles,
        body_class="antialiased",
        page_script_tag=script_tag,
    )

    return HTMLResponse(
        content=html,
        status_code=200,
        headers={
            "Content-Security-Policy": build_preview_csp(api_origin),
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        },
    )


@router.get("/draft/{project_id}.js")
async def serve_draft_script(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Serve the draft JS file (requires auth)."""
    project = get_project(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    draft_version_id = project.get("draftVersionId")
    version = get_version_by_id(project_id, draft_version_id) if draft_version_id else None
    if not version:
        version = get_current_version_data(project_id)
    if not version:
        raise HTTPException(status_code=404, detail="Draft not found")

    if not version.js:
        return Response(status_code=204)

    return Response(
        content=version.js,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-store",
        },
    )
from ..models.user import get_current_user
from .projects import get_project
from .versions import get_current_version_data, get_version_by_id
