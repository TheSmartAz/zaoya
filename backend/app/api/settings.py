"""Settings endpoints for user preferences."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.db import User
from app.models.user import get_current_user_db

router = APIRouter(prefix="/api/settings", tags=["settings"])


class UserSettings(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    # Language
    language: str = "en"
    auto_detect_language: bool = True

    # AI Model
    preferred_model: str = "glm-4.7"
    model_region: str = "auto"

    # Default design system
    default_design_system: Optional[dict] = None

    # Notifications
    email_enabled: bool = True
    email_submission_notifications: bool = True
    email_weekly_analytics: bool = False
    email_project_updates: bool = False
    notification_email: Optional[str] = None

    browser_notifications_enabled: bool = True
    browser_notify_submissions: bool = True
    browser_notify_published: bool = True
    browser_notify_generation: bool = False


DEFAULT_SETTINGS = UserSettings()


def _extract_settings(preferences: dict | None) -> dict:
    if not isinstance(preferences, dict):
        return {}

    stored = preferences.get("settings")
    if isinstance(stored, dict):
        return stored

    # Backward-compatible fallback for flat storage.
    keys = DEFAULT_SETTINGS.model_dump().keys()
    if any(key in preferences for key in keys):
        return {key: preferences.get(key) for key in keys if key in preferences}

    return {}


def _merge_settings(raw: dict | None) -> UserSettings:
    data = DEFAULT_SETTINGS.model_dump()
    if isinstance(raw, dict):
        data.update(raw)
    return UserSettings.model_validate(data)


@router.get("/", response_model=UserSettings)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db),
) -> UserSettings:
    """Get user settings."""
    _ = db
    settings_data = _extract_settings(current_user.preferences or {})
    return _merge_settings(settings_data)


@router.put("/", response_model=UserSettings)
async def update_settings(
    settings: UserSettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db),
) -> UserSettings:
    """Update user settings."""
    payload = settings.model_dump()
    if payload.get("notification_email") == "":
        payload["notification_email"] = None

    preferences = current_user.preferences or {}
    preferences["settings"] = payload
    current_user.preferences = preferences

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return UserSettings.model_validate(payload)
