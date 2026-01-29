"""Internal API endpoints for edge server (Caddy)."""

import re
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.db import CustomDomain
from app.models.schemas import DomainCheckResponse


router = APIRouter()


def verify_edge_secret(request: Request):
    """Dependency to verify edge server authentication."""
    provided = request.headers.get("X-Zaoya-Edge-Secret")

    if not settings.zaoya_edge_secret:
        raise HTTPException(
            status_code=500, detail="Edge secret not configured on server"
        )

    if provided != settings.zaoya_edge_secret:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Optional: Verify source IP
    if settings.allowed_edge_ips:
        client_ip = request.client.host if request.client else None
        forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")

        request_ip = real_ip or forwarded_for or client_ip
        if request_ip not in settings.allowed_edge_ips:
            raise HTTPException(status_code=403, detail="Forbidden")


def normalize_and_validate_domain(domain: str) -> str:
    """Normalize and strictly validate domain input."""
    if not domain:
        raise HTTPException(status_code=400, detail="Domain required")

    # Normalize
    domain = domain.lower().strip().rstrip(".")

    # Length check
    if len(domain) > 253:
        raise HTTPException(status_code=400, detail="Domain too long")

    # ASCII only
    if not domain.isascii():
        raise HTTPException(status_code=400, detail="Invalid domain")

    # Format check (strict)
    pattern = r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
    if not re.match(pattern, domain):
        raise HTTPException(status_code=400, detail="Invalid domain format")

    # No ports
    if ":" in domain:
        raise HTTPException(status_code=400, detail="Invalid domain")

    return domain


@router.get("/domain/check")
async def check_domain(
    domain: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_edge_secret),  # Security check
) -> DomainCheckResponse:
    """
    Called by Caddy to verify if a domain should be issued an SSL certificate.
    Protected by shared secret.
    """
    # Validate and normalize input
    domain = normalize_and_validate_domain(domain)

    # Look up domain
    result = await db.execute(
        select(CustomDomain)
        .where(CustomDomain.domain == domain)
        .where(CustomDomain.verification_status.in_(["verified", "active"]))
    )
    custom_domain = result.scalar_one_or_none()

    if not custom_domain:
        return DomainCheckResponse(
            valid=False, reason="Domain not found or not verified"
        )

    # Update SSL status on first successful check
    if custom_domain.ssl_status == "pending":
        custom_domain.ssl_status = "provisioning"
        await db.commit()

    return DomainCheckResponse(
        valid=True,
        project_id=str(custom_domain.project_id),
        is_apex=custom_domain.is_apex,
    )


@router.post("/domain/{domain}/ssl-active")
async def mark_ssl_active(
    domain: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_edge_secret),  # Security check
):
    """Called by Caddy after successful SSL provisioning."""
    domain = normalize_and_validate_domain(domain)

    result = await db.execute(
        select(CustomDomain).where(CustomDomain.domain == domain)
    )
    custom_domain = result.scalar_one_or_none()

    if custom_domain:
        custom_domain.ssl_status = "active"
        custom_domain.ssl_provisioned_at = datetime.utcnow()
        if custom_domain.verification_status == "verified":
            custom_domain.verification_status = "active"
        await db.commit()

    return {"status": "ok"}


@router.post("/domain/{domain}/ssl-error")
async def mark_ssl_error(
    domain: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_edge_secret),  # Security check
):
    """Called by Caddy when SSL provisioning fails."""
    domain = normalize_and_validate_domain(domain)

    result = await db.execute(
        select(CustomDomain).where(CustomDomain.domain == domain)
    )
    custom_domain = result.scalar_one_or_none()

    if custom_domain:
        custom_domain.ssl_status = "error"
        custom_domain.failure_reason = "SSL certificate provisioning failed"
        await db.commit()

    return {"status": "ok"}
