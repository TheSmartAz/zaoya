"""Assets API for managing image library."""

from datetime import datetime, date
from pathlib import Path
from io import BytesIO
import re
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.db import Asset, Project
from app.config import settings
from app.models.user import get_current_user
from app.services.storage_service import StorageService


# ============================================================
# Request/Response Models
# ============================================================

class UpdateAssetRequest(BaseModel):
    """Request to update asset metadata."""
    alt_text: Optional[str] = None
    tags: Optional[list[str]] = None


class ListAssetsQuery:
    """Query parameters for listing assets."""
    def __init__(
        self,
        asset_type: Optional[str] = None,
        project_id: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ):
        self.asset_type = asset_type
        self.project_id = project_id
        self.tag = tag
        self.search = search
        self.limit = min(limit, 100)
        self.offset = offset


router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _sanitize_filename(name: str) -> str:
    """Sanitize filenames to avoid unsafe characters."""
    name = name.strip().replace(" ", "_")
    return re.sub(r"[^a-zA-Z0-9._-]", "", name)


def _get_image_dimensions(data: bytes) -> tuple[int | None, int | None]:
    """Get image dimensions if possible."""
    try:
        from PIL import Image
    except ImportError:
        return None, None

    try:
        with Image.open(BytesIO(data)) as img:
            return img.width, img.height
    except Exception:
        return None, None


def _generate_thumbnail(data: bytes, max_size: int = 400) -> bytes | None:
    """Generate a thumbnail image (returns bytes) or None if unavailable."""
    try:
        from PIL import Image
    except ImportError:
        return None

    try:
        with Image.open(BytesIO(data)) as img:
            img.thumbnail((max_size, max_size))
            output = BytesIO()
            format_name = "PNG" if img.mode in ("RGBA", "P") else "JPEG"
            if format_name == "JPEG":
                img = img.convert("RGB")
            img.save(output, format_name, quality=85)
            return output.getvalue()
    except Exception:
        return None


# ============================================================
# Helper Functions
# ============================================================

async def get_user_id(current_user: dict, db: AsyncSession) -> UUID:
    """Get UUID for current user."""
    from app.models.db import User

    try:
        uid = UUID(current_user["id"])
    except ValueError:
        if current_user.get("provider") == "dev":
            result = await db.execute(
                select(User).where(User.email == current_user["email"])
            )
            user = result.scalar_one_or_none()
            if user:
                return user.id
        raise HTTPException(status_code=401, detail="Invalid user")

    return uid


# ============================================================
# Asset CRUD Endpoints
# ============================================================

@router.get("/assets")
async def list_assets(
    asset_type: Optional[str] = None,
    project_id: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's assets with filtering."""
    user_id = await get_user_id(current_user, db)

    # Build query
    query = select(Asset).where(Asset.user_id == user_id)

    # Apply filters
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)

    if project_id:
        try:
            pid = UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project ID")
        query = query.where(or_(Asset.project_id == pid, Asset.project_id.is_(None)))

    if tag:
        query = query.where(Asset.tags.contains([tag]))

    if search:
        query = query.where(
            or_(
                Asset.alt_text.ilike(f"%{search}%"),
                Asset.original_filename.ilike(f"%{search}%"),
            )
        )

    # Order by created date desc, with pagination
    query = query.order_by(Asset.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    assets = list(result.scalars())

    # Get total count
    # Rebuild the base query for counting
    count_query_base = select(Asset).where(Asset.user_id == user_id)

    if asset_type:
        count_query_base = count_query_base.where(Asset.asset_type == asset_type)
    if project_id:
        try:
            pid = UUID(project_id)
        except ValueError:
            pid = None
        count_query_base = count_query_base.where(or_(Asset.project_id == pid, Asset.project_id.is_(None)))
    if tag:
        count_query_base = count_query_base.where(Asset.tags.contains([tag]))
    if search:
        count_query_base = count_query_base.where(
            or_(
                Asset.alt_text.ilike(f"%{search}%"),
                Asset.original_filename.ilike(f"%{search}%"),
            )
        )

    count_result = await db.execute(select(func.count()).select_from(count_query_base))
    total = count_result.scalar() or 0

    usage_result = await db.execute(
        select(
            func.coalesce(func.sum(Asset.file_size_bytes), 0),
            func.count(Asset.id),
        ).where(Asset.user_id == user_id)
    )
    usage_row = usage_result.first()
    total_bytes = usage_row[0] if usage_row else 0

    return {
        "assets": [
            {
                "id": str(asset.id),
                "asset_type": asset.asset_type,
                "url": asset.url,
                "thumbnail_url": asset.thumbnail_url,
                "original_filename": asset.original_filename,
                "prompt": asset.prompt,
                "generation_provider": asset.generation_provider,
                "width": asset.width,
                "height": asset.height,
                "alt_text": asset.alt_text,
                "tags": asset.tags or [],
                "project_id": str(asset.project_id) if asset.project_id else None,
                "created_at": asset.created_at.isoformat(),
            }
            for asset in assets
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "usage": {
            "total_bytes": int(total_bytes or 0),
            "total_assets": int(total or 0),
        },
    }


@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific asset."""
    user_id = await get_user_id(current_user, db)

    try:
        aid = UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid asset ID")

    result = await db.execute(
        select(Asset).where(
            and_(
                Asset.id == aid,
                Asset.user_id == user_id
            )
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return {
        "id": str(asset.id),
        "asset_type": asset.asset_type,
        "url": asset.url,
        "thumbnail_url": asset.thumbnail_url,
        "original_filename": asset.original_filename,
        "prompt": asset.prompt,
        "generation_provider": asset.generation_provider,
        "generation_metadata": asset.generation_metadata,
        "width": asset.width,
        "height": asset.height,
        "mime_type": asset.mime_type,
        "alt_text": asset.alt_text,
        "tags": asset.tags or [],
        "file_size_bytes": asset.file_size_bytes,
        "project_id": str(asset.project_id) if asset.project_id else None,
        "created_at": asset.created_at.isoformat(),
    }


@router.post("/assets/upload")
async def upload_asset(
    file: UploadFile,
    project_id: Optional[str] = None,
    alt_text: Optional[str] = None,
    tags: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload an image asset to the library."""
    user_id = await get_user_id(current_user, db)

    # Parse tags
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Parse project_id
    pid = UUID(project_id) if project_id else None

    storage = StorageService()

    original_name = _sanitize_filename(file.filename or "upload")
    ext = Path(original_name).suffix or ""
    filename = f"{uuid4().hex}{ext}"
    key = f"{user_id}/{filename}"

    content = await file.read()
    url = await storage.save_bytes(key, content, file.content_type)

    thumbnail_url = None
    thumbnail_key = None
    thumb_bytes = _generate_thumbnail(content)
    if thumb_bytes:
        thumb_name = f"{uuid4().hex}_thumb.jpg"
        thumbnail_key = f"{user_id}/thumbs/{thumb_name}"
        thumbnail_url = await storage.save_bytes(thumbnail_key, thumb_bytes, "image/jpeg")

    width, height = _get_image_dimensions(content)

    asset = Asset(
        id=uuid4(),
        user_id=user_id,
        project_id=pid,
        asset_type="uploaded",
        url=url,
        thumbnail_url=thumbnail_url or url,
        original_filename=file.filename,
        alt_text=alt_text,
        tags=tag_list,
        file_size_bytes=len(content),
        mime_type=file.content_type,
        width=width,
        height=height,
        generation_metadata={
            "storage_key": key,
            "thumbnail_key": thumbnail_key,
            "backend": storage.backend,
        },
        created_at=datetime.utcnow(),
    )

    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return {
        "id": str(asset.id),
        "url": asset.url,
        "original_filename": asset.original_filename,
        "tags": asset.tags or [],
    }


@router.patch("/assets/{asset_id}")
async def update_asset(
    asset_id: str,
    request: UpdateAssetRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update asset metadata."""
    user_id = await get_user_id(current_user, db)

    try:
        aid = UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid asset ID")

    result = await db.execute(
        select(Asset).where(
            and_(
                Asset.id == aid,
                Asset.user_id == user_id
            )
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if request.alt_text is not None:
        asset.alt_text = request.alt_text
    if request.tags is not None:
        asset.tags = request.tags

    await db.commit()
    await db.refresh(asset)

    return {
        "id": str(asset.id),
        "alt_text": asset.alt_text,
        "tags": asset.tags or [],
    }


@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an asset from the library."""
    user_id = await get_user_id(current_user, db)

    try:
        aid = UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid asset ID")

    result = await db.execute(
        select(Asset).where(
            and_(
                Asset.id == aid,
                Asset.user_id == user_id
            )
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    storage = StorageService()
    metadata = asset.generation_metadata or {}
    storage_key = metadata.get("storage_key")
    thumbnail_key = metadata.get("thumbnail_key")
    try:
        if storage_key:
            await storage.delete(storage_key)
        if thumbnail_key:
            await storage.delete(thumbnail_key)
    except Exception:
        # Ignore storage cleanup failures
        pass

    await db.delete(asset)
    await db.commit()

    return {"deleted": True}


@router.get("/assets/tags")
async def list_tags(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all tags used by user's assets."""
    user_id = await get_user_id(current_user, db)

    # Get all assets with tags
    result = await db.execute(
        select(Asset.tags).where(
            and_(
                Asset.user_id == user_id,
                Asset.tags.isnot(None),
                Asset.tags != []
            )
        )
    )

    all_tags = set()
    for (tags,) in result:
        if tags:
            all_tags.update(tags)

    return {
        "tags": sorted(list(all_tags)),
    }


# ============================================================
# Project Assets Endpoints
# ============================================================

@router.get("/projects/{project_id}/assets")
async def list_project_assets(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List assets associated with a specific project."""
    from app.models.db import User

    # Get user
    try:
        uid = UUID(current_user["id"])
    except ValueError:
        if current_user.get("provider") == "dev":
            user_result = await db.execute(
                select(User).where(User.email == current_user["email"])
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=401, detail="Invalid user")
            uid = user.id
        else:
            raise HTTPException(status_code=401, detail="Invalid user")

    # Verify project ownership
    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid project ID")

    project_result = await db.execute(
        select(Project).where(
            and_(
                Project.id == pid,
                Project.user_id == uid
            )
        )
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get assets for this project
    result = await db.execute(
        select(Asset)
        .where(
            and_(
                Asset.user_id == uid,
                Asset.project_id == pid
            )
        )
        .order_by(Asset.created_at.desc())
    )

    assets = []
    for asset in result.scalars():
        assets.append({
            "id": str(asset.id),
            "asset_type": asset.asset_type,
            "url": asset.url,
            "thumbnail_url": asset.thumbnail_url,
            "alt_text": asset.alt_text,
            "width": asset.width,
            "height": asset.height,
            "tags": asset.tags or [],
            "created_at": asset.created_at.isoformat(),
        })

    return {"assets": assets}
