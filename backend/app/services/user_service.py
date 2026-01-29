"""User service for database-backed user management."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.db import User
from app.services.auth_service import auth_service


class UserService:
    """Service for managing user accounts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID | str) -> User | None:
        """Get a user by ID."""
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return None

        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_provider(
        self, provider: str, provider_id: str
    ) -> User | None:
        """Get a user by OAuth provider."""
        result = await self.db.execute(
            select(User).where(
                User.provider == provider,
                User.provider_id == provider_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create_email_user(
        self,
        email: str,
        password: str,
        name: str | None = None,
    ) -> User:
        """
        Create a new user with email/password authentication.

        Raises:
            ValueError: If email already exists
        """
        # Check if user exists
        existing = await self.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        user = User(
            id=uuid4(),
            email=email,
            password_hash=auth_service.hash_password(password),
            name=name,
            provider="email",
            created_at=datetime.utcnow(),
        )

        self.db.add(user)
        try:
            await self.db.commit()
            await self.db.refresh(user)
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Email already registered")

        return user

    async def create_oauth_user(
        self,
        email: str,
        provider: str,
        provider_id: str,
        name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """
        Create or link an OAuth user.

        Returns the existing user if already linked, or creates a new one.
        """
        # Check for existing user by provider
        existing = await self.get_by_provider(provider, provider_id)
        if existing:
            # Update profile data
            if name:
                existing.name = name
            if avatar_url:
                existing.avatar_url = avatar_url
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        # Check if email exists but with different provider
        existing_email = await self.get_by_email(email)
        if existing_email:
            # Link the provider to existing account
            existing_email.provider = provider
            existing_email.provider_id = provider_id
            if name:
                existing_email.name = name
            if avatar_url:
                existing_email.avatar_url = avatar_url
            await self.db.commit()
            await self.db.refresh(existing_email)
            return existing_email

        # Create new user
        user = User(
            id=uuid4(),
            email=email,
            provider=provider,
            provider_id=provider_id,
            name=name,
            avatar_url=avatar_url,
            created_at=datetime.utcnow(),
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def verify_password(self, email: str, password: str) -> User | None:
        """
        Verify email/password credentials.

        Returns the user if valid, None otherwise.
        """
        user = await self.get_by_email(email)
        if not user or not user.password_hash:
            return None

        if auth_service.verify_password(password, user.password_hash):
            return user

        return None

    async def update_user(
        self,
        user_id: UUID,
        name: str | None = None,
        avatar_url: str | None = None,
        preferences: dict | None = None,
    ) -> User:
        """Update user profile."""
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if name is not None:
            user.name = name
        if avatar_url is not None:
            user.avatar_url = avatar_url
        if preferences is not None:
            user.preferences = preferences

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def set_username(self, user_id: UUID, username: str) -> User:
        """Set a unique username for a user."""
        # Check if username is taken
        existing = await self.get_by_username(username)
        if existing and existing.id != user_id:
            raise ValueError("Username already taken")

        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.username = username
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> None:
        """Change user password."""
        user = await self.get_by_id(user_id)
        if not user or not user.password_hash:
            raise ValueError("User not found or has no password")

        if not auth_service.verify_password(old_password, user.password_hash):
            raise ValueError("Invalid current password")

        user.password_hash = auth_service.hash_password(new_password)
        await self.db.commit()

    def to_dict(self, user: User) -> dict:
        """Convert user to dictionary for API responses."""
        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url,
            "provider": user.provider,
            "username": user.username,
            "preferences": user.preferences or {},
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    async def get_or_create_dev_user(self) -> User:
        """Get or create the development user for testing."""
        dev_email = "dev@zaoya.app"
        user = await self.get_by_email(dev_email)

        if not user:
            user = User(
                id=uuid4(),
                email=dev_email,
                name="Dev User",
                provider="dev",
                created_at=datetime.utcnow(),
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

        return user
