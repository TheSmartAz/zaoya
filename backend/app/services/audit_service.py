"""Service for audit event logging."""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.audit_event import AuditEvent


class AuditService:
    """Service for logging audit events."""

    @staticmethod
    async def log(
        db: AsyncSession,
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        team_id: Optional[UUID] = None,
        meta_data: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
            db: Database session
            action: Action performed (e.g., "domain.added")
            resource_type: Type of resource (e.g., "custom_domain")
            resource_id: ID of the resource
            user_id: ID of the user who performed the action
            team_id: ID of the team (future)
            meta_data: Additional context as JSON
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditEvent
        """
        event = AuditEvent(
            user_id=user_id,
            team_id=team_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            meta_data=meta_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(event)
        await db.flush()  # Get ID without committing
        return event

    @staticmethod
    async def log_domain_added(
        db: AsyncSession,
        domain_id: UUID,
        user_id: UUID,
        domain: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditEvent:
        """Log a domain added event."""
        return await AuditService.log(
            db=db,
            action=AuditEvent.Actions.DOMAIN_ADDED,
            resource_type=AuditEvent.ResourceTypes.CUSTOM_DOMAIN,
            resource_id=domain_id,
            user_id=user_id,
            meta_data={"domain": domain},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def log_domain_verified(
        db: AsyncSession,
        domain_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> AuditEvent:
        """Log a domain verified event."""
        return await AuditService.log(
            db=db,
            action=AuditEvent.Actions.DOMAIN_VERIFIED,
            resource_type=AuditEvent.ResourceTypes.CUSTOM_DOMAIN,
            resource_id=domain_id,
            user_id=user_id,
        )

    @staticmethod
    async def log_domain_removed(
        db: AsyncSession,
        domain_id: UUID,
        user_id: UUID,
        domain: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditEvent:
        """Log a domain removed event."""
        return await AuditService.log(
            db=db,
            action=AuditEvent.Actions.DOMAIN_REMOVED,
            resource_type=AuditEvent.ResourceTypes.CUSTOM_DOMAIN,
            resource_id=domain_id,
            user_id=user_id,
            meta_data={"domain": domain},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def log_domain_verification_failed(
        db: AsyncSession,
        domain_id: UUID,
        reason: str,
    ) -> AuditEvent:
        """Log a domain verification failed event."""
        return await AuditService.log(
            db=db,
            action=AuditEvent.Actions.DOMAIN_VERIFICATION_FAILED,
            resource_type=AuditEvent.ResourceTypes.CUSTOM_DOMAIN,
            resource_id=domain_id,
            meta_data={"reason": reason},
        )
