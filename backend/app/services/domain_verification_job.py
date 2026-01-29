"""Background job for verifying custom domains."""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select

from app.config import settings
from app.db import AsyncSessionLocal
from app.models.db import CustomDomain, Project
from app.services.audit_service import AuditService
from app.services.domain_service import DomainService

logger = logging.getLogger(__name__)


async def _verify_pending_domains_once() -> None:
    """Run a single verification pass for pending domains."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CustomDomain, Project.user_id)
            .join(Project, Project.id == CustomDomain.project_id)
            .where(CustomDomain.verification_status == "pending")
        )
        rows = result.all()

        if not rows:
            return

        now = datetime.utcnow()

        for custom_domain, user_id in rows:
            try:
                if custom_domain.is_expired:
                    custom_domain.verification_status = "failed"
                    custom_domain.failure_reason = "Verification period expired"
                    custom_domain.last_checked_at = now
                    custom_domain.attempt_count += 1
                    await AuditService.log_domain_verification_failed(
                        db=db,
                        domain_id=custom_domain.id,
                        reason=custom_domain.failure_reason,
                    )
                    continue

                verification = await DomainService.verify_domain(
                    custom_domain.domain,
                    custom_domain.verification_token,
                )

                custom_domain.last_checked_at = now
                custom_domain.attempt_count += 1

                if verification.get("verified"):
                    custom_domain.verification_status = "verified"
                    custom_domain.verified_at = now
                    custom_domain.failure_reason = None
                    await AuditService.log_domain_verified(
                        db=db,
                        domain_id=custom_domain.id,
                        user_id=user_id,
                    )
                else:
                    custom_domain.failure_reason = "TXT record not found"
            except Exception as exc:
                logger.warning(
                    "Domain verification failed for %s: %s",
                    custom_domain.domain,
                    exc,
                )

        await db.commit()


async def run_domain_verification_loop() -> None:
    """Continuously verify pending domains at a fixed interval."""
    interval = max(60, settings.domain_verification_interval_seconds)
    while True:
        try:
            await _verify_pending_domains_once()
        except Exception as exc:
            logger.warning("Domain verification job error: %s", exc)
        await asyncio.sleep(interval)
