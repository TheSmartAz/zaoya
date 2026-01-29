"""Username and slug validation endpoints."""

import re
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import get_current_user_db
from app.models.db import User

router = APIRouter(tags=["users"])

RESERVED_WORDS = {
    'admin', 'api', 'www', 'app', 'help', 'support', 'about', 'contact',
    'home', 'blog', 'shop', 'store', 'cart', 'user', 'users', 'auth',
    'login', 'signup', 'dashboard', 'settings', 'profile', 'search',
    'p', 'u', 'assets', 'static', 'cdn', 'media', 'images',
    'css', 'js', 'fonts', 'health', 'status', 'ping', 'robots',
    'sitemap', 'favicon', 'manifest', 'service-worker', 'sw',
}

USERNAME_PATTERN = r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'
USERNAME_MIN_LEN = 3
USERNAME_MAX_LEN = 30
SLUG_PATTERN = r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'
USERNAME_CHANGE_COOLDOWN_DAYS = 30
USERNAME_CHANGED_AT_KEY = "username_changed_at"


@router.get("/auth/username/available/{username}")
async def check_username_available(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """Check if a username is available."""
    # Normalize to lowercase
    username = username.lower()

    # Validate length + format
    if not (USERNAME_MIN_LEN <= len(username) <= USERNAME_MAX_LEN):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-30 characters, lowercase alphanumeric with hyphens"
        )
    if not re.match(USERNAME_PATTERN, username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-30 characters, lowercase alphanumeric with hyphens"
        )

    # Check reserved words
    if username in RESERVED_WORDS:
        raise HTTPException(
            status_code=400,
            detail="This username is not available"
        )

    # Check if already taken
    result = await db.execute(
        select(User).where(User.username == username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

    return {"available": True}


@router.put("/auth/username")
async def set_username(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Set or change username."""
    from datetime import datetime, timedelta
    from uuid import UUID

    username = request.get("username", "").lower().strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    # Validate length + format
    if not (USERNAME_MIN_LEN <= len(username) <= USERNAME_MAX_LEN):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-30 characters, lowercase alphanumeric with hyphens"
        )
    if not re.match(USERNAME_PATTERN, username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-30 characters, lowercase alphanumeric with hyphens"
        )

    # Check reserved words
    if username in RESERVED_WORDS:
        raise HTTPException(
            status_code=400,
            detail="This username is not available"
        )

    # Check if already taken (by another user)
    result = await db.execute(
        select(User).where(User.username == username, User.id != current_user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

    if current_user.username == username:
        return {"username": username}

    # Enforce cooldown for username changes
    prefs = current_user.preferences or {}
    last_changed_raw = prefs.get(USERNAME_CHANGED_AT_KEY)
    if current_user.username and last_changed_raw:
        try:
            last_changed_at = datetime.fromisoformat(last_changed_raw)
            if datetime.utcnow() - last_changed_at < timedelta(days=USERNAME_CHANGE_COOLDOWN_DAYS):
                raise HTTPException(
                    status_code=400,
                    detail=f"Username can be changed every {USERNAME_CHANGE_COOLDOWN_DAYS} days"
                )
        except ValueError:
            # Ignore malformed timestamps
            pass

    # Update user
    current_user.username = username
    prefs[USERNAME_CHANGED_AT_KEY] = datetime.utcnow().isoformat()
    current_user.preferences = prefs
    await db.commit()

    return {"username": username}
