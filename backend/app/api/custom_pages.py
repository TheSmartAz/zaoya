"""Custom domain page serving routes.

These are catch-all routes that serve published pages for custom domains.
They should be registered LAST in the application so other routes take priority.
"""

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.csp import build_publish_csp
from app.db import get_db
from app.models.db import Project, CustomDomain

router = APIRouter()

PUBLISH_DIR = Path(__file__).resolve().parents[2] / "published_pages"


def _get_api_base() -> str:
    return settings.api_url.rstrip("/")


def _origin_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return url


def _build_csp_header(api_origin: str) -> str:
    return build_publish_csp(api_origin)


def _safe_publish_path(public_id: str, path: str) -> Optional[Path]:
    """Safely resolve a path within the publish directory."""
    base_dir = (PUBLISH_DIR / public_id).resolve()
    candidate = (base_dir / path).resolve()
    if base_dir not in candidate.parents and base_dir != candidate:
        return None
    return candidate


def _serve_file(public_id: str, path: str, api_origin: str) -> Response:
    """Serve a file from the published pages directory."""
    target = _safe_publish_path(public_id, path)
    if not target or not target.exists():
        raise HTTPException(status_code=404, detail="Page not found")

    if target.suffix == ".js":
        return Response(
            content=target.read_text(encoding="utf-8"),
            media_type="application/javascript",
            headers={"Cache-Control": "no-store"},
        )

    html = target.read_text(encoding="utf-8")
    return HTMLResponse(
        content=html,
        status_code=200,
        headers={
            "Content-Security-Policy": _build_csp_header(api_origin),
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        },
    )


async def _get_project_by_custom_domain(
    domain: str, db: AsyncSession
) -> tuple[Optional[Project], Optional[CustomDomain]]:
    """Get project and custom domain record by domain name."""
    result = await db.execute(
        select(CustomDomain).where(
            CustomDomain.domain == domain.lower(),
            CustomDomain.verification_status.in_(["verified", "active"]),
        )
    )
    custom_domain = result.scalar_one_or_none()

    if not custom_domain:
        return None, None

    result = await db.execute(
        select(Project).where(
            Project.id == custom_domain.project_id,
            Project.status == "published",
        )
    )
    project = result.scalar_one_or_none()

    return project, custom_domain


def _check_www_redirect(request: Request, custom_domain: CustomDomain) -> Optional[str]:
    """
    Check if we need to redirect www to apex.

    Canonical URL Policy (deterministic, no user config):
    - If apex domain is configured (is_apex=True), www.{domain} redirects to {domain}
    - If subdomain is configured, no automatic redirect
    """
    if not custom_domain.is_apex:
        return None

    # Get the original host from X-Custom-Domain header (set by Caddy)
    original_host = request.headers.get("X-Custom-Domain", "").lower().strip()

    # Check if request is for www.{apex_domain}
    if original_host.startswith("www."):
        apex_domain = original_host[4:]  # Remove "www." prefix
        if apex_domain == custom_domain.domain:
            # Build redirect URL to apex
            path = request.url.path
            query = request.url.query
            redirect_url = f"https://{custom_domain.domain}{path}"
            if query:
                redirect_url += f"?{query}"
            return redirect_url

    return None


async def _serve_custom_domain_page(
    request: Request,
    path: str,
    db: AsyncSession,
) -> Response:
    """Serve a page via custom domain."""
    domain = getattr(request.state, "custom_domain", None)
    if not domain:
        raise HTTPException(status_code=404, detail="Page not found")

    project, custom_domain = await _get_project_by_custom_domain(domain, db)

    if not project or not custom_domain or not project.public_id:
        raise HTTPException(status_code=404, detail="Page not found")

    # Check for www→apex redirect (if apex domain is configured)
    redirect_url = _check_www_redirect(request, custom_domain)
    if redirect_url:
        return RedirectResponse(url=redirect_url, status_code=301)

    api_origin = _origin_from_url(_get_api_base())

    # Serve the file
    if path.endswith(".js"):
        return _serve_file(project.public_id, path, api_origin)

    normalized = path.strip("/")
    if not normalized:
        return _serve_file(project.public_id, "index.html", api_origin)
    return _serve_file(project.public_id, f"{normalized}/index.html", api_origin)


@router.get("/", include_in_schema=False)
async def serve_custom_domain_root(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Catch-all for root "/" on custom domains.

    Only activates if request.state.is_custom_domain is True.
    """
    if not getattr(request.state, "is_custom_domain", False):
        # Not a custom domain request - 404 so other handlers can match
        # (This shouldn't be reached as other routes should match first)
        raise HTTPException(status_code=404, detail="Not found")

    return await _serve_custom_domain_page(request, "", db)


@router.get("/{path:path}", include_in_schema=False)
async def serve_custom_domain_path(
    request: Request,
    path: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Catch-all for any path on custom domains.

    Only activates if request.state.is_custom_domain is True.
    """
    if not getattr(request.state, "is_custom_domain", False):
        raise HTTPException(status_code=404, detail="Not found")

    return await _serve_custom_domain_page(request, path, db)
