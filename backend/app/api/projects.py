"""Project API endpoints for CRUD and publishing."""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
import secrets
import string

from ..config import settings
from ..models.user import get_current_user
from ..services.validator import process_generation
from .versions import get_current_version_data, get_version_by_id

router = APIRouter()

# In-memory storage (replace with database in production)
_projects_storage: Dict[str, dict] = {}

# Published versions storage
_published_pages: Dict[str, dict] = {}


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


@router.post("/projects")
async def create_project(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a new project."""
    import time
    requested_id = request.get("id")
    if requested_id and requested_id in _projects_storage:
        raise HTTPException(status_code=400, detail="Project ID already exists")

    project_id = requested_id or f"proj_{int(time.time())}_{secrets.token_hex(4)}"

    project = {
        "id": project_id,
        "userId": current_user["id"],
        "name": request.get("name"),
        "templateId": request.get("template_id"),
        "templateInputs": request.get("template_inputs", {}),
        "status": "draft",
        "draftVersionId": None,
        "publishedVersionId": None,
        "publicId": None,
        "publishedAt": None,
        "notification_email": None,
        "notification_enabled": False,
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat(),
    }

    _projects_storage[project_id] = project

    return {
        "id": project["id"],
        "name": project["name"],
        "template_id": project["templateId"],
        "template_inputs": project["templateInputs"],
        "status": project["status"],
        "public_id": project.get("publicId"),
        "published_url": project.get("publishedUrl"),
        "notification_email": project.get("notification_email"),
        "notification_enabled": project.get("notification_enabled", False),
        "created_at": project["createdAt"],
        "updated_at": project["updatedAt"],
    }


@router.get("/projects")
async def list_projects(current_user: dict = Depends(get_current_user)):
    """List all projects for the current user."""
    projects = get_user_projects(current_user["id"])
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "template_id": p["templateId"],
            "template_inputs": p["templateInputs"],
            "status": p["status"],
            "public_id": p.get("publicId"),
            "published_url": p.get("publishedUrl"),
            "notification_email": p.get("notification_email"),
            "notification_enabled": p.get("notification_enabled", False),
            "created_at": p["createdAt"],
            "updated_at": p["updatedAt"],
        }
        for p in projects
    ]


@router.get("/projects/{project_id}")
async def get_project_details(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get project details."""
    project = get_project(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": project["id"],
        "name": project["name"],
        "template_id": project["templateId"],
        "template_inputs": project["templateInputs"],
        "status": project["status"],
        "public_id": project.get("publicId"),
        "published_url": project.get("publishedUrl"),
        "notification_email": project.get("notification_email"),
        "notification_enabled": project.get("notification_enabled", False),
        "created_at": project["createdAt"],
        "updated_at": project["updatedAt"],
    }


@router.patch("/projects/{project_id}")
async def update_project(
    project_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user),
):
    """Update project settings (currently notification settings)."""
    project = get_project(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if "notification_email" in request:
        email = request.get("notification_email")
        project["notification_email"] = email or None

    if "notification_enabled" in request:
        project["notification_enabled"] = bool(request.get("notification_enabled"))

    if project.get("notification_enabled") and not project.get("notification_email"):
        project["notification_enabled"] = False

    project["updatedAt"] = datetime.utcnow().isoformat()

    return {
        "id": project["id"],
        "name": project["name"],
        "template_id": project["templateId"],
        "template_inputs": project["templateInputs"],
        "status": project["status"],
        "public_id": project.get("publicId"),
        "published_url": project.get("publishedUrl"),
        "notification_email": project.get("notification_email"),
        "notification_enabled": project.get("notification_enabled", False),
        "created_at": project["createdAt"],
        "updated_at": project["updatedAt"],
    }


@router.post("/projects/{project_id}/publish")
async def publish_project(
    project_id: str,
    _request: Optional[dict] = None,
    current_user: dict = Depends(get_current_user)
):
    """Publish a project."""
    project = get_project(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    draft_version_id = project.get("draftVersionId")
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
    if not project.get("publicId"):
        project["publicId"] = generate_public_id()

    # Store the published page (immutable snapshot)
    _published_pages[project["publicId"]] = {
        "projectId": project_id,
        "html": sanitized_html,
        "js": sanitized_js or None,
        "metadata": {
            "title": project["name"],
            "publicId": project["publicId"],
            "publishedAt": datetime.utcnow().isoformat(),
        }
    }

    # Update project
    project["status"] = "published"
    project["publishedVersionId"] = version.id
    project["publishedAt"] = datetime.utcnow().isoformat()
    project["updatedAt"] = datetime.utcnow().isoformat()

    # Generate the URL (published pages host)
    base_url = settings.pages_url.rstrip("/")
    published_url = f"{base_url}/p/{project['publicId']}"

    project["publishedUrl"] = published_url

    return {
        "publicId": project["publicId"],
        "publishedAt": project["publishedAt"],
        "url": published_url,
    }


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a project."""
    project = get_project(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Also delete published page if exists
    if project.get("publicId"):
        _published_pages.pop(project["publicId"], None)

    _projects_storage.pop(project_id, None)

    return {"deleted": True}
