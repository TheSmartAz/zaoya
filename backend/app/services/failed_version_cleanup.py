"""Cleanup job for failed version attempts."""

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import delete

from app.db import AsyncSessionLocal
from app.models.db import VersionAttempt

logger = logging.getLogger(__name__)


async def cleanup_failed_versions(max_age_days: int = 90) -> int:
    """Delete failed version attempts older than max_age_days."""
    cutoff = datetime.utcnow() - timedelta(days=max_age_days)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(VersionAttempt).where(VersionAttempt.created_at < cutoff)
        )
        await db.commit()
        return result.rowcount or 0


async def run_failed_version_cleanup_loop(
    interval_seconds: int = 24 * 60 * 60,
    max_age_days: int = 90,
) -> None:
    """Continuously cleanup failed versions at a fixed interval."""
    while True:
        try:
            deleted = await cleanup_failed_versions(max_age_days=max_age_days)
            if deleted:
                logger.info("Failed version cleanup removed %s rows", deleted)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed version cleanup error: %s", exc)
        await asyncio.sleep(interval_seconds)
