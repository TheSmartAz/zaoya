from __future__ import annotations

import base64
from io import BytesIO

from PIL import Image
from playwright.async_api import async_playwright


class ThumbnailService:
    """Generate page thumbnails using a headless browser."""

    VIEWPORT_WIDTH = 390
    VIEWPORT_HEIGHT = 844
    THUMBNAIL_WIDTH = 160
    THUMBNAIL_HEIGHT = 347

    async def generate_thumbnail(self, html: str, page_id: str, project_id: str) -> str:
        """Generate thumbnail from HTML content and return a data URL."""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page(
                    viewport={
                        "width": self.VIEWPORT_WIDTH,
                        "height": self.VIEWPORT_HEIGHT,
                    },
                    device_scale_factor=2,
                )

                await page.set_content(html, wait_until="networkidle")
                await page.wait_for_timeout(500)

                screenshot = await page.screenshot(type="png", full_page=False)
            finally:
                await browser.close()

        thumbnail = self._resize_to_thumbnail(screenshot)
        return await self._store_thumbnail(thumbnail, page_id, project_id)

    def _resize_to_thumbnail(self, screenshot_bytes: bytes) -> bytes:
        img = Image.open(BytesIO(screenshot_bytes))
        resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
        img = img.resize(
            (self.THUMBNAIL_WIDTH * 2, self.THUMBNAIL_HEIGHT * 2),
            resample,
        )

        output = BytesIO()
        img.save(output, format="PNG", optimize=True)
        return output.getvalue()

    async def _store_thumbnail(self, thumbnail_bytes: bytes, page_id: str, project_id: str) -> str:
        b64 = base64.b64encode(thumbnail_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"


thumbnail_service = ThumbnailService()
