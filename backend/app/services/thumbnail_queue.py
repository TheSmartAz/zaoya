"""Thumbnail/OG image queue processing."""

from __future__ import annotations

import asyncio
import base64
import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import Literal
from uuid import UUID, uuid4

from PIL import Image
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models.db import Project, ProjectPage, Snapshot, Page
from app.models.db.thumbnail_job import ThumbnailJob
from app.services.storage_service import StorageService
from app.services.template_renderer import build_inline_styles, strip_script_tags
from app.services.validator import extract_body_content

logger = logging.getLogger(__name__)

JobType = Literal["thumbnail", "og_image"]

THUMBNAIL_VIEWPORT = (375, 667)
THUMBNAIL_SIZE = (300, 600)
OG_VIEWPORT = (1200, 630)
OG_SIZE = (1200, 630)

MAX_CONCURRENT = 2
CAPTURE_TIMEOUT_MS = 30_000

BACKOFF_SECONDS = [30, 45, 60]


def _now() -> datetime:
    return datetime.utcnow()


def _build_design_css(design_system: dict) -> str:
    colors = (design_system or {}).get("colors", {}) if isinstance(design_system, dict) else {}
    typography = (design_system or {}).get("typography", {}) if isinstance(design_system, dict) else {}
    spacing = (design_system or {}).get("spacing", "comfortable")
    border_radius = (design_system or {}).get("border_radius", "medium")
    animation_level = (design_system or {}).get("animation_level", "subtle")

    css_vars = []
    for key, value in colors.items():
        css_vars.append(f"--color-{key}: {value};")

    heading = typography.get("heading", {}) if isinstance(typography, dict) else {}
    body = typography.get("body", {}) if isinstance(typography, dict) else {}
    if heading:
        css_vars.append(f"--font-heading-family: {heading.get('family', 'Inter')};")
        css_vars.append(f"--font-heading-size: {heading.get('size', 'large')};")
        css_vars.append(f"--font-heading-weight: {heading.get('weight', 600)};")
        css_vars.append(f"--font-heading-line-height: {heading.get('line_height', 1.4)};")
    if body:
        css_vars.append(f"--font-body-family: {body.get('family', 'Inter')};")
        css_vars.append(f"--font-body-size: {body.get('size', 'medium')};")
        css_vars.append(f"--font-body-weight: {body.get('weight', 400)};")
        css_vars.append(f"--font-body-line-height: {body.get('line_height', 1.6)};")

    spacing_map = {
        "compact": "12px",
        "comfortable": "16px",
        "spacious": "20px",
    }
    radius_map = {
        "none": "0px",
        "small": "4px",
        "medium": "8px",
        "large": "16px",
        "full": "9999px",
    }
    animation_map = {
        "none": "0ms",
        "subtle": "150ms",
        "moderate": "250ms",
        "energetic": "400ms",
    }

    css_vars.append(f"--spacing-base: {spacing_map.get(spacing, '16px')};")
    css_vars.append(f"--radius-base: {radius_map.get(border_radius, '8px')};")
    css_vars.append(f"--animation-duration: {animation_map.get(animation_level, '150ms')};")

    return f"""
:root {{
  {chr(10).join(css_vars)}
}}
"""


def _capture_document(body_html: str, styles: str, title: str = "Zaoya") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    {styles}
  </head>
  <body class="bg-white antialiased">
    {body_html}
  </body>
</html>"""


def _resize_png(data: bytes, width: int, height: int) -> bytes:
    img = Image.open(BytesIO(data))
    resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
    img = img.resize((width, height), resample)
    output = BytesIO()
    img.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _placeholder_svg(
    text: str,
    width: int,
    height: int,
    background: str = "#f3f4f6",
    foreground: str = "#111827",
) -> bytes:
    safe_text = (text or "Untitled")[:40]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="{background}"/>
  <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" fill="{foreground}" font-family="Arial, sans-serif" font-size="32">
    {safe_text}
  </text>
</svg>"""
    return svg.encode("utf-8")


def _decode_data_url(data_url: str) -> tuple[bytes, str]:
    if not data_url.startswith("data:"):
        raise ValueError("Invalid data URL")
    header, b64data = data_url.split(",", 1)
    mime = header.split(";")[0].replace("data:", "")
    return base64.b64decode(b64data), mime


def _storage_key(job_type: JobType, project_id: UUID, page_id: UUID, ext: str) -> str:
    folder = "thumbnails" if job_type == "thumbnail" else "og-images"
    safe_ext = ext.lstrip(".") or "png"
    return f"{folder}/{project_id}/{page_id}.{safe_ext}"


def _backoff_delay(attempts: int) -> int:
    if attempts <= 0:
        return 0
    idx = min(attempts - 1, len(BACKOFF_SECONDS) - 1)
    return BACKOFF_SECONDS[idx]


class ThumbnailQueue:
    """DB-backed queue processor for thumbnails + OG images."""

    def __init__(self) -> None:
        self._running = False
        self._lock = asyncio.Lock()
        self._inflight = {"thumbnail": 0, "og_image": 0}
        self._limits = {"thumbnail": MAX_CONCURRENT, "og_image": MAX_CONCURRENT}

    async def start(self) -> None:
        async with self._lock:
            if self._running:
                return
            self._running = True
            asyncio.create_task(self._worker_loop("thumbnail"))
            asyncio.create_task(self._worker_loop("og_image"))

    async def enqueue_thumbnail(
        self,
        db: AsyncSession,
        project_id: UUID,
        page_id: UUID,
        delay_seconds: int = 0,
    ) -> ThumbnailJob:
        return await self._enqueue_job(db, project_id, page_id, "thumbnail", delay_seconds)

    async def enqueue_og_image(
        self,
        db: AsyncSession,
        project_id: UUID,
        page_id: UUID,
        delay_seconds: int = 0,
    ) -> ThumbnailJob:
        return await self._enqueue_job(db, project_id, page_id, "og_image", delay_seconds)

    async def get_latest_job(
        self,
        db: AsyncSession,
        project_id: UUID,
        page_id: UUID,
        job_type: JobType,
    ) -> ThumbnailJob | None:
        result = await db.execute(
            select(ThumbnailJob)
            .where(
                ThumbnailJob.project_id == project_id,
                ThumbnailJob.page_id == page_id,
                ThumbnailJob.type == job_type,
            )
            .order_by(ThumbnailJob.updated_at.desc(), ThumbnailJob.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def bump_job_priority(
        self,
        db: AsyncSession,
        project_id: UUID,
        page_id: UUID,
        job_type: JobType,
    ) -> None:
        now = _now()
        await db.execute(
            update(ThumbnailJob)
            .where(
                ThumbnailJob.project_id == project_id,
                ThumbnailJob.page_id == page_id,
                ThumbnailJob.type == job_type,
                ThumbnailJob.status == "queued",
            )
            .values(next_run_at=now, updated_at=now)
        )
        await db.commit()

    async def generate_og_image_now(
        self,
        project_id: UUID,
        page_id: UUID,
    ) -> str | None:
        async with AsyncSessionLocal() as db:
            job = await self._enqueue_job(db, project_id, page_id, "og_image", 0)
            try:
                image_url = await self._process_og_job(db, job)
                await self._mark_done(db, job, image_url)
                return image_url
            except Exception as exc:  # noqa: BLE001
                await self._mark_failed_or_retry(db, job, str(exc))
                return job.image_url

    async def process_job_now(self, job_id: UUID) -> str | None:
        async with AsyncSessionLocal() as db:
            job = await db.get(ThumbnailJob, job_id)
            if not job:
                return None
            now = _now()
            job.status = "running"
            job.updated_at = now
            await db.commit()
            await db.refresh(job)

            try:
                if job.type == "thumbnail":
                    image_url = await self._process_thumbnail_job(db, job)
                else:
                    image_url = await self._process_og_job(db, job)
                await self._mark_done(db, job, image_url)
                return image_url
            except Exception as exc:  # noqa: BLE001
                await self._mark_failed_or_retry(db, job, str(exc))
                return job.image_url

    async def store_client_image(
        self,
        db: AsyncSession,
        project_id: UUID,
        page_id: UUID,
        job_type: JobType,
        data_url: str,
    ) -> ThumbnailJob:
        payload, mime = _decode_data_url(data_url)
        ext = "png"
        if mime == "image/jpeg":
            ext = "jpg"
        elif mime == "image/svg+xml":
            ext = "svg"

        if mime in {"image/png", "image/jpeg"}:
            try:
                img = Image.open(BytesIO(payload))
                resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
                target = THUMBNAIL_SIZE if job_type == "thumbnail" else OG_SIZE
                img = img.resize((target[0], target[1]), resample)
                output = BytesIO()
                img.save(output, format="PNG", optimize=True)
                payload = output.getvalue()
                mime = "image/png"
                ext = "png"
            except Exception:
                pass
        key = _storage_key(job_type, project_id, page_id, ext)
        storage = StorageService()
        image_url = await storage.save_bytes(key, payload, mime)

        await db.execute(
            update(ThumbnailJob)
            .where(
                ThumbnailJob.project_id == project_id,
                ThumbnailJob.page_id == page_id,
                ThumbnailJob.type == job_type,
                ThumbnailJob.status.in_(["queued", "running"]),
            )
            .values(status="failed", last_error="superseded by client upload", updated_at=_now())
        )

        job = ThumbnailJob(
            id=uuid4(),
            project_id=project_id,
            page_id=page_id,
            type=job_type,
            status="done",
            attempts=1,
            max_attempts=1,
            next_run_at=None,
            last_error=None,
            image_url=image_url,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(job)

        if job_type == "thumbnail":
            await db.execute(
                update(ProjectPage)
                .where(ProjectPage.id == page_id)
                .values(thumbnail_url=image_url, updated_at=_now())
            )

        await db.commit()
        await db.refresh(job)
        return job

    async def _enqueue_job(
        self,
        db: AsyncSession,
        project_id: UUID,
        page_id: UUID,
        job_type: JobType,
        delay_seconds: int = 0,
    ) -> ThumbnailJob:
        now = _now()
        await db.execute(
            update(ThumbnailJob)
            .where(
                ThumbnailJob.project_id == project_id,
                ThumbnailJob.page_id == page_id,
                ThumbnailJob.type == job_type,
                ThumbnailJob.status.in_(["queued", "running"]),
            )
            .values(status="failed", last_error="superseded by new job", updated_at=now)
        )

        if job_type == "thumbnail":
            await db.execute(
                update(ProjectPage)
                .where(ProjectPage.id == page_id)
                .values(thumbnail_url=None, updated_at=now)
            )

        job = ThumbnailJob(
            id=uuid4(),
            project_id=project_id,
            page_id=page_id,
            type=job_type,
            status="queued",
            attempts=0,
            max_attempts=3,
            next_run_at=now + timedelta(seconds=delay_seconds) if delay_seconds else now,
            created_at=now,
            updated_at=now,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def _worker_loop(self, job_type: JobType) -> None:
        while True:
            try:
                if self._inflight[job_type] >= self._limits[job_type]:
                    await asyncio.sleep(0.5)
                    continue
                job = await self._claim_job(job_type)
                if not job:
                    await asyncio.sleep(1)
                    continue
                self._inflight[job_type] += 1
                asyncio.create_task(self._run_job(job.id, job_type))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Thumbnail worker error (%s): %s", job_type, exc)
                await asyncio.sleep(1)

    async def _claim_job(self, job_type: JobType) -> ThumbnailJob | None:
        now = _now()
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ThumbnailJob)
                .where(
                    ThumbnailJob.type == job_type,
                    ThumbnailJob.status == "queued",
                    or_(ThumbnailJob.next_run_at.is_(None), ThumbnailJob.next_run_at <= now),
                )
                .order_by(ThumbnailJob.next_run_at.asc().nullsfirst(), ThumbnailJob.created_at.asc())
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            job = result.scalars().first()
            if not job:
                return None
            job.status = "running"
            job.updated_at = now
            await db.commit()
            await db.refresh(job)
            return job

    async def _run_job(self, job_id: UUID, job_type: JobType) -> None:
        try:
            async with AsyncSessionLocal() as db:
                job = await db.get(ThumbnailJob, job_id)
                if not job:
                    return
                if job_type == "thumbnail":
                    image_url = await self._process_thumbnail_job(db, job)
                else:
                    image_url = await self._process_og_job(db, job)
                await self._mark_done(db, job, image_url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Thumbnail job failed (%s): %s", job_id, exc)
            async with AsyncSessionLocal() as db:
                job = await db.get(ThumbnailJob, job_id)
                if job:
                    await self._mark_failed_or_retry(db, job, str(exc))
        finally:
            self._inflight[job_type] -= 1

    async def _process_thumbnail_job(self, db: AsyncSession, job: ThumbnailJob) -> str:
        page = await db.get(ProjectPage, job.page_id)
        if not page or page.project_id != job.project_id:
            raise ValueError("Page not found for thumbnail job")

        html = (page.content or {}).get("html") if isinstance(page.content, dict) else None
        if not html:
            raise ValueError("No HTML available for thumbnail")

        body_html = strip_script_tags(extract_body_content(html))
        design_css = _build_design_css(page.design_system or {})
        styles = build_inline_styles(body_html, design_css)
        document = _capture_document(body_html, styles, title=page.name)

        screenshot = await self._capture_screenshot(
            document,
            viewport=THUMBNAIL_VIEWPORT,
            full_page=True,
        )
        resized = _resize_png(screenshot, THUMBNAIL_SIZE[0], THUMBNAIL_SIZE[1])

        storage = StorageService()
        key = _storage_key("thumbnail", job.project_id, job.page_id, "png")
        return await storage.save_bytes(key, resized, "image/png")

    async def _process_og_job(self, db: AsyncSession, job: ThumbnailJob) -> str:
        project = await db.get(Project, job.project_id)
        if not project or not project.published_snapshot_id:
            raise ValueError("Project not published")

        page = await db.get(Page, job.page_id)
        if not page or page.snapshot_id != project.published_snapshot_id:
            raise ValueError("Published page not found")

        snapshot = await db.get(Snapshot, page.snapshot_id)
        design_css = _build_design_css(snapshot.design_system if snapshot else {})

        body_html = strip_script_tags(extract_body_content(page.html or ""))
        styles = build_inline_styles(body_html, design_css)
        document = _capture_document(body_html, styles, title=page.title or project.name)

        screenshot = await self._capture_screenshot(
            document,
            viewport=OG_VIEWPORT,
            full_page=False,
        )
        resized = _resize_png(screenshot, OG_SIZE[0], OG_SIZE[1])

        storage = StorageService()
        key = _storage_key("og_image", job.project_id, job.page_id, "png")
        return await storage.save_bytes(key, resized, "image/png")

    async def _capture_screenshot(
        self,
        html: str,
        *,
        viewport: tuple[int, int],
        full_page: bool,
    ) -> bytes:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page(
                    viewport={"width": viewport[0], "height": viewport[1]},
                    device_scale_factor=2,
                )
                page.set_default_timeout(CAPTURE_TIMEOUT_MS)
                await page.set_content(html, wait_until="networkidle")
                await page.wait_for_timeout(300)
                return await page.screenshot(type="png", full_page=full_page)
            except PlaywrightTimeoutError as exc:
                raise TimeoutError("Screenshot timed out") from exc
            finally:
                await browser.close()

    async def _mark_done(self, db: AsyncSession, job: ThumbnailJob, image_url: str) -> None:
        now = _now()
        job.status = "done"
        job.image_url = image_url
        job.updated_at = now
        job.last_error = None
        job.next_run_at = None
        if job.type == "thumbnail":
            await db.execute(
                update(ProjectPage)
                .where(ProjectPage.id == job.page_id)
                .values(thumbnail_url=image_url, updated_at=now)
            )
        await db.commit()

    async def _mark_failed_or_retry(self, db: AsyncSession, job: ThumbnailJob, error: str) -> None:
        now = _now()
        job.attempts += 1
        if job.attempts < job.max_attempts:
            delay = _backoff_delay(job.attempts)
            job.status = "queued"
            job.next_run_at = now + timedelta(seconds=delay)
            job.last_error = error
            job.updated_at = now
            await db.commit()
            return

        # Final fallback: SVG placeholder
        placeholder_url = None
        try:
            title = ""
            background = "#f3f4f6"
            if job.type == "thumbnail":
                page = await db.get(ProjectPage, job.page_id)
                title = page.name if page else "Untitled"
                colors = (page.design_system or {}).get("colors", {}) if page else {}
                background = colors.get("background", background)
            else:
                page = await db.get(Page, job.page_id)
                title = page.title if page else "Untitled"
                if page:
                    snapshot = await db.get(Snapshot, page.snapshot_id)
                    colors = (snapshot.design_system or {}).get("colors", {}) if snapshot else {}
                    background = colors.get("background", background)

            svg_bytes = _placeholder_svg(
                title,
                THUMBNAIL_SIZE[0] if job.type == "thumbnail" else OG_SIZE[0],
                THUMBNAIL_SIZE[1] if job.type == "thumbnail" else OG_SIZE[1],
                background=background,
            )
            storage = StorageService()
            key = _storage_key(job.type, job.project_id, job.page_id, "svg")
            placeholder_url = await storage.save_bytes(key, svg_bytes, "image/svg+xml")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to generate placeholder: %s", exc)

        job.status = "failed"
        job.last_error = error
        job.image_url = placeholder_url
        job.updated_at = now
        job.next_run_at = None
        if job.type == "thumbnail" and placeholder_url:
            await db.execute(
                update(ProjectPage)
                .where(ProjectPage.id == job.page_id)
                .values(thumbnail_url=placeholder_url, updated_at=now)
            )
        await db.commit()


thumbnail_queue = ThumbnailQueue()


async def ensure_thumbnail_workers_running() -> None:
    await thumbnail_queue.start()
