"""Centralized access control service for permission checks."""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.project import Project
from app.models.db.user import User


class Permission:
    """Permission constants."""

    PROJECT_VIEW = "project:view"
    PROJECT_EDIT = "project:edit"
    PROJECT_DELETE = "project:delete"
    PROJECT_PUBLISH = "project:publish"
    DOMAIN_MANAGE = "domain:manage"


class AccessControlService:
    """
    Centralized permission checks.
    Currently user-only; ready for team RBAC extension.
    """

    @staticmethod
    async def can_access_project(
        db: AsyncSession,
        user: User,
        project: Project,
        permission: str,
    ) -> bool:
        """
        Check if user has permission on project.
        For v1: Owner has all permissions.
        For v2+: Will check team membership and roles.
        """
        # v1: Simple owner check
        if project.user_id == user.id:
            return True

        # Future: Check team membership
        # if project.owner_type == "team":
        #     member = await get_team_member(db, project.owner_id, user.id)
        #     if member:
        #         return permission in get_role_permissions(member.role)

        return False

    @staticmethod
    async def require_project_access(
        db: AsyncSession,
        user: User,
        project: Project,
        permission: str,
    ) -> None:
        """Raise HTTPException if access denied."""
        if not await AccessControlService.can_access_project(
            db, user, project, permission
        ):
            raise HTTPException(status_code=403, detail="Access denied")
