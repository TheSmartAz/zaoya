"""User Pydantic models for API requests/responses."""

import os
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..services.auth_service import auth_service
from app.db import get_db
from app.models.db import User as DbUser

AUTH_BYPASS_ENV = os.getenv("ZAOYA_BYPASS_AUTH", "")
AUTH_BYPASS = AUTH_BYPASS_ENV.lower() in {"1", "true", "yes", "on"} or settings.environment == "development"
security = HTTPBearer(auto_error=False)

DEV_USER = {
    "id": "dev-user",
    "email": "dev@zaoya.app",
    "name": "Dev User",
    "avatar_url": None,
    "provider": "dev",
}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Return the current user or a dev stub when auth is bypassed."""
    if AUTH_BYPASS:
        return DEV_USER

    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = auth_service.verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "id": user_id,
        "email": None,
        "name": None,
        "avatar_url": None,
        "provider": "token",
    }


async def get_current_user_db(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DbUser:
    """Return the current user from the database (create dev user if needed)."""
    user_id = current_user.get("id")
    user_uuid: UUID | None = None
    if user_id:
        try:
            user_uuid = UUID(str(user_id))
        except ValueError:
            user_uuid = None

    if user_uuid:
        result = await db.execute(select(DbUser).where(DbUser.id == user_uuid))
        user = result.scalar_one_or_none()
        if user:
            return user

    email = current_user.get("email")
    if current_user.get("provider") == "dev" and email:
        result = await db.execute(select(DbUser).where(DbUser.email == email))
        user = result.scalar_one_or_none()
        if user:
            return user

        user = DbUser(
            email=email,
            name=current_user.get("name"),
            provider="dev",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    raise HTTPException(status_code=401, detail="Invalid user")


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    """User creation model."""
    password: str


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    """Google OAuth request."""
    credential: str


class UserResponse(UserBase):
    """User response model."""
    id: str
    avatar_url: Optional[str] = None
    provider: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response."""
    token: str
    user: UserResponse


class TokenPayload(BaseModel):
    """Token payload."""
    sub: str
    exp: int
    iat: int
