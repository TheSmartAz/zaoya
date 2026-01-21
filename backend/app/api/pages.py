"""Published page serving API endpoints."""

import os
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse

from ..models.user import get_current_user
from .projects import get_project
from .versions import get_current_version_data, get_version_by_id

router = APIRouter()

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


def build_csp_header(api_origin: str) -> str:
    connect_src = api_origin if api_origin else "'self'"
    return "; ".join([
        "default-src 'none'",
        "img-src 'self' data: blob: https:",
        "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com",
        "script-src 'self' https://cdn.tailwindcss.com",
        f"connect-src {connect_src}",
        "frame-ancestors 'none'",
    ])


def build_published_html(
    html_content: str,
    js_content: Optional[str],
    metadata: dict,
    api_base: str,
) -> str:
    """Build full HTML document for a published page."""
    title = metadata.get('title', 'Zaoya Page')
    public_id = metadata.get('publicId', '')

    # Open Graph metadata
    og_title = title
    og_description = metadata.get('description', 'Created with Zaoya - Describe it. See it. Share it.')
    og_image = metadata.get('ogImage', '')

    script_tag = f'<script src="/p/{public_id}.js" defer></script>' if js_content else ''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{og_description}">

    <!-- Zaoya Configuration -->
    <meta name="zaoya-public-id" content="{public_id}">
    <meta name="zaoya-api-base" content="{api_base}">

    <!-- Open Graph -->
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{og_description}">
    <meta property="og:image" content="{og_image}">
    <meta property="og:type" content="website">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{og_title}">
    <meta name="twitter:description" content="{og_description}">
    <meta name="twitter:image" content="{og_image}">

    <!-- Tailwind CDN -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Zaoya Runtime -->
    <script src="/zaoya-runtime.js" defer></script>
</head>
<body class="antialiased">
    {html_content}
    {script_tag}
</body>
</html>'''


def build_draft_html(
    html_content: str,
    js_content: Optional[str],
    project_id: str,
    title: str,
) -> str:
    script_tag = f'<script src="/draft/{project_id}.js" defer></script>' if js_content else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} (Draft)</title>

    <!-- Tailwind CDN -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Zaoya Runtime -->
    <script src="/zaoya-runtime.js" defer></script>
</head>
<body class="antialiased">
    {html_content}
    {script_tag}
</body>
</html>'''


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

    html = build_published_html(
        html_content=page_data['html'],
        js_content=page_data.get('js'),
        metadata=page_data['metadata'],
        api_base=api_base,
    )

    return HTMLResponse(
        content=html,
        status_code=200,
        headers={
            "Content-Security-Policy": build_csp_header(api_origin),
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

    html = build_draft_html(
        html_content=version.html,
        js_content=version.js,
        project_id=project_id,
        title=project.get("name", "Zaoya Draft"),
    )

    return HTMLResponse(
        content=html,
        status_code=200,
        headers={
            "Content-Security-Policy": build_csp_header(api_origin),
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
