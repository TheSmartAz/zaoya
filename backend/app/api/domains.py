"""Custom domain API endpoints."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.db import Project, CustomDomain, User
from app.models.schemas import (
    AddDomainRequest,
    DomainResponse,
    VerifyDomainResponse,
    DnsInstructions,
    DnsInstructionSet,
    DnsRecord,
)
from app.models.user import get_current_user_db
from app.services.domain_service import DomainService
from app.services.access_control import AccessControlService, Permission
from app.services.audit_service import AuditService
from app.services.subscription_service import SubscriptionService


router = APIRouter()


def _get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user agent from request."""
    ip = request.headers.get("X-Real-IP") or (
        request.client.host if request.client else None
    )
    user_agent = request.headers.get("User-Agent")
    return ip, user_agent


def _build_domain_response(domain: CustomDomain) -> DomainResponse:
    """Build a domain response with DNS instructions."""
    instructions = DomainService.get_dns_instructions(
        domain.domain, domain.verification_token
    )

    return DomainResponse(
        id=domain.id,
        domain=domain.domain,
        is_apex=domain.is_apex,
        verification_status=domain.verification_status,
        verification_expires_at=domain.verification_expires_at,
        ssl_status=domain.ssl_status,
        dns_instructions=DnsInstructions(
            recommended=DnsInstructionSet(
                description=instructions["recommended"]["description"],
                records=[
                    DnsRecord(**r) for r in instructions["recommended"]["records"]
                ],
            ),
            apex=DnsInstructionSet(
                description=instructions["apex"]["description"],
                records=[DnsRecord(**r) for r in instructions["apex"]["records"]],
            ),
            help_text=instructions["help_text"],
        ),
        created_at=domain.created_at,
        verified_at=domain.verified_at,
        ssl_provisioned_at=domain.ssl_provisioned_at,
        attempt_count=domain.attempt_count,
        failure_reason=domain.failure_reason,
    )


@router.post("/projects/{project_id}/domain", status_code=201)
async def add_domain(
    project_id: str,
    request_body: AddDomainRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db),
):
    """Add a custom domain to a project."""
    # Parse and validate project ID
    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get project
    result = await db.execute(select(Project).where(Project.id == pid))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check access
    await AccessControlService.require_project_access(
        db, current_user, project, Permission.DOMAIN_MANAGE
    )

    # Enforce subscription limits for custom domains
    subscription_service = SubscriptionService(db)
    _, limits = await subscription_service.get_user_subscription(current_user.id)
    custom_domain_enabled = limits.get("custom_domain")
    if not custom_domain_enabled:
        raise HTTPException(
            status_code=403,
            detail="Custom domains are not available on your current plan",
        )

    # Domain limits follow project limits (1 domain per project)
    domain_limit = limits.get("projects")
    if isinstance(custom_domain_enabled, (int, float)) and not isinstance(custom_domain_enabled, bool):
        domain_limit = int(custom_domain_enabled)

    if domain_limit != -1 and isinstance(domain_limit, int):
        # Count existing custom domains for this user
        count_result = await db.execute(
            select(func.count(CustomDomain.id))
            .select_from(CustomDomain)
            .join(Project, Project.id == CustomDomain.project_id)
            .where(Project.user_id == current_user.id)
        )
        current_count = count_result.scalar() or 0
        if current_count >= domain_limit:
            raise HTTPException(
                status_code=403,
                detail="Custom domain limit reached for your plan",
            )

    # Check if project already has a domain (1:1 mapping)
    result = await db.execute(
        select(CustomDomain).where(CustomDomain.project_id == pid)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409, detail="Project already has a custom domain configured"
        )

    # Validate domain format
    domain = DomainService.normalize_domain(request_body.domain)
    is_valid, error_msg = DomainService.validate_domain(domain)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Check if domain is already in use
    result = await db.execute(
        select(CustomDomain).where(CustomDomain.domain == domain)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Domain is already in use by another project"
        )

    # Create custom domain record
    token = DomainService.generate_verification_token()
    is_apex = DomainService.is_apex_domain(domain)

    custom_domain = CustomDomain(
        project_id=pid,
        domain=domain,
        is_apex=is_apex,
        verification_token=token,
        verification_status="pending",
        verification_expires_at=datetime.utcnow() + timedelta(days=7),
        ssl_status="pending",
    )

    db.add(custom_domain)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail="Domain is already in use by another project"
        )

    await db.refresh(custom_domain)

    # Log audit event
    ip, user_agent = _get_client_info(request)
    await AuditService.log_domain_added(
        db,
        domain_id=custom_domain.id,
        user_id=current_user.id,
        domain=domain,
        ip_address=ip,
        user_agent=user_agent,
    )
    await db.commit()

    return _build_domain_response(custom_domain)


@router.get("/projects/{project_id}/domain")
async def get_domain(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db),
):
    """Get custom domain configuration for a project."""
    # Parse and validate project ID
    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get project
    result = await db.execute(select(Project).where(Project.id == pid))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check access
    await AccessControlService.require_project_access(
        db, current_user, project, Permission.PROJECT_VIEW
    )

    # Get custom domain
    result = await db.execute(
        select(CustomDomain).where(CustomDomain.project_id == pid)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="No custom domain configured")

    return _build_domain_response(domain)


@router.post("/projects/{project_id}/domain/verify")
async def verify_domain(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db),
):
    """Manually trigger domain verification check."""
    # Parse and validate project ID
    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get project
    result = await db.execute(select(Project).where(Project.id == pid))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check access
    await AccessControlService.require_project_access(
        db, current_user, project, Permission.DOMAIN_MANAGE
    )

    # Get custom domain
    result = await db.execute(
        select(CustomDomain).where(CustomDomain.project_id == pid)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="No custom domain configured")

    # Check if already verified/active
    if domain.verification_status in ("verified", "active"):
        return VerifyDomainResponse(
            verification_status=domain.verification_status,
            attempt_count=domain.attempt_count,
            message="Domain is already verified",
            verified_at=domain.verified_at,
        )

    # Check if verification expired
    if domain.verification_status == "pending" and domain.is_expired:
        domain.verification_status = "failed"
        domain.failure_reason = "Verification period expired"
        await db.commit()
        return VerifyDomainResponse(
            verification_status="failed",
            attempt_count=domain.attempt_count,
            message="Verification period has expired. Please remove and re-add the domain.",
        )

    # Perform verification
    verification = await DomainService.verify_domain(
        domain.domain, domain.verification_token
    )

    domain.last_checked_at = datetime.utcnow()
    domain.attempt_count += 1

    if verification["verified"]:
        domain.verification_status = "verified"
        domain.verified_at = datetime.utcnow()
        domain.failure_reason = None

        # Log audit event
        await AuditService.log_domain_verified(
            db, domain_id=domain.id, user_id=current_user.id
        )
        await db.commit()

        return VerifyDomainResponse(
            verification_status="verified",
            attempt_count=domain.attempt_count,
            message="Domain verified successfully! SSL certificate will be provisioned on first request.",
            verified_at=domain.verified_at,
            checks=verification["checks"],
        )
    else:
        await db.commit()
        return VerifyDomainResponse(
            verification_status="pending",
            attempt_count=domain.attempt_count,
            message="DNS records not found. Please check your configuration.",
            checks=verification["checks"],
        )


@router.delete("/projects/{project_id}/domain", status_code=204)
async def delete_domain(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db),
):
    """Remove custom domain from project."""
    # Parse and validate project ID
    try:
        pid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get project
    result = await db.execute(select(Project).where(Project.id == pid))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check access
    await AccessControlService.require_project_access(
        db, current_user, project, Permission.DOMAIN_MANAGE
    )

    # Get custom domain
    result = await db.execute(
        select(CustomDomain).where(CustomDomain.project_id == pid)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="No custom domain configured")

    # Log audit event before deletion
    ip, user_agent = _get_client_info(request)
    await AuditService.log_domain_removed(
        db,
        domain_id=domain.id,
        user_id=current_user.id,
        domain=domain.domain,
        ip_address=ip,
        user_agent=user_agent,
    )

    # Delete domain
    await db.delete(domain)
    await db.commit()

    return None
