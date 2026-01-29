"""Version API endpoints for managing page snapshots."""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from ..models import Version, CreateVersionRequest, RestoreVersionRequest, ListVersionsResponse
from ..services.validator import process_generation

router = APIRouter()

# In-memory storage (replace with database in production)
_versions_storage: Dict[str, List[Version]] = {}
_version_counters: Dict[str, int] = {}
_current_versions: Dict[str, str] = {}


def _generate_version_id() -> str:
    """Generate a unique version ID."""
    import time
    import random
    return f"{int(time.time())}-{random.randint(1000, 9999)}"


def get_version_by_id(project_id: str, version_id: str) -> Optional[Version]:
    """Get a version by ID for a project."""
    for version in _versions_storage.get(project_id, []):
        if version.id == version_id:
            return version
    return None


def get_current_version_data(project_id: str) -> Optional[Version]:
    """Get the current version for a project."""
    current_id = _current_versions.get(project_id)
    if not current_id:
        return None
    return get_version_by_id(project_id, current_id)


@router.post("/versions", response_model=Version)
async def create_version(request: CreateVersionRequest):
    """Create a new version for a project."""
    project_id = request.projectId

    # Initialize project storage if needed
    if project_id not in _versions_storage:
        _versions_storage[project_id] = []
        _version_counters[project_id] = 0

    # Increment version number
    _version_counters[project_id] += 1
    version_number = _version_counters[project_id]

    is_valid, sanitized_html, sanitized_js, errors = process_generation(
        request.html,
        request.js,
    )
    if not is_valid:
        raise HTTPException(status_code=422, detail={"errors": errors})

    # Create version
    version = Version(
        id=_generate_version_id(),
        projectId=project_id,
        number=version_number,
        html=sanitized_html,
        js=sanitized_js or None,
        metadata=request.metadata,
    )

    # Store version
    _versions_storage[project_id].append(version)
    _current_versions[project_id] = version.id

    # Update project draft pointer if the project exists
    try:
        from .projects import _projects_storage
        project = _projects_storage.get(project_id)
        if project:
            project["draftVersionId"] = version.id
            project["status"] = "draft"
            project["updatedAt"] = datetime.utcnow().isoformat()
    except Exception:
        pass

    return version


@router.get("/versions/{project_id}", response_model=ListVersionsResponse)
async def list_versions(project_id: str):
    """Get all versions for a project."""
    versions = _versions_storage.get(project_id, [])
    current_id = _current_versions.get(project_id)

    return ListVersionsResponse(
        versions=versions,
        currentVersionId=current_id,
    )


@router.post("/versions/restore", response_model=Version)
async def restore_version(request: RestoreVersionRequest):
    """Restore a previous version by creating a new version with its content."""
    # Find the version across all projects
    found_version = None
    found_project_id = None

    for project_id, versions in _versions_storage.items():
        for v in versions:
            if v.id == request.versionId:
                found_version = v
                found_project_id = project_id
                break
        if found_version:
            break

    if not found_version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Create a new version with the restored content
    return await create_version(CreateVersionRequest(
        projectId=found_project_id,
        html=found_version.html,
        js=found_version.js,
        metadata={
            "prompt": f"Restored from version {found_version.number}",
            "timestamp": int(__import__("time").time() * 1000),
            "changeType": "restore",
        },
    ))


@router.get("/versions/{project_id}/current")
async def get_current_version(project_id: str):
    """Get the current version for a project."""
    current_id = _current_versions.get(project_id)
    if not current_id:
        raise HTTPException(status_code=404, detail="No current version")

    versions = _versions_storage.get(project_id, [])
    for v in versions:
        if v.id == current_id:
            return v

    raise HTTPException(status_code=404, detail="Current version not found")


@router.delete("/versions/{project_id}")
async def delete_project_versions(project_id: str):
    """Delete all versions for a project (useful for cleanup)."""
    if project_id in _versions_storage:
        del _versions_storage[project_id]
    if project_id in _version_counters:
        del _version_counters[project_id]
    if project_id in _current_versions:
        del _current_versions[project_id]

    return {"deleted": True}
