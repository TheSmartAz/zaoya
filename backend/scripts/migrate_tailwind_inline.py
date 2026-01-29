"""Migrate stored HTML to remove Tailwind CDN and inline runtime helpers.

Usage:
  python backend/scripts/migrate_tailwind_inline.py
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models.db import Page, ProjectPage
from app.services.template_renderer import (
    build_inline_styles,
    get_runtime_script_tag,
    strip_script_tags,
)
from app.services.validator import extract_body_content

TAILWIND_CDN_PATTERN = re.compile(
    r"<script[^>]*src=[\"']https://cdn\.tailwindcss\.com[\"'][^>]*></script>",
    re.IGNORECASE,
)
RUNTIME_SCRIPT_PATTERN = re.compile(
    r"<script[^>]*src=[\"'][^\"']*zaoya-runtime\.js[^\"']*[\"'][^>]*></script>",
    re.IGNORECASE,
)


def _strip_tailwind_cdn(html: str) -> str:
    return TAILWIND_CDN_PATTERN.sub("", html)


def _strip_runtime_script(html: str) -> str:
    return RUNTIME_SCRIPT_PATTERN.sub("", html)


def _insert_after_head(html: str, snippet: str) -> str:
    if "<head" not in html:
        return snippet + html
    return re.sub(
        r"(<head[^>]*>)",
        r"\1\n" + snippet,
        html,
        count=1,
        flags=re.IGNORECASE,
    )


def _insert_before_body_end(html: str, snippet: str) -> str:
    if "</body>" not in html:
        return html + snippet
    return re.sub(r"</body>", snippet + "\n</body>", html, count=1, flags=re.IGNORECASE)


async def _migrate_db() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ProjectPage))
        pages = list(result.scalars().all())
        for page in pages:
            content = page.content or {}
            html = content.get("html")
            if not html:
                continue
            cleaned = _strip_tailwind_cdn(strip_script_tags(html))
            if cleaned != html:
                page.content = {**content, "html": cleaned}

        result = await db.execute(select(Page))
        snapshot_pages = list(result.scalars().all())
        for page in snapshot_pages:
            html = page.html or ""
            cleaned = _strip_tailwind_cdn(strip_script_tags(html))
            if cleaned != html:
                page.html = cleaned

        await db.commit()


def _migrate_published_files() -> None:
    published_dir = Path(__file__).resolve().parents[1] / "published_pages"
    if not published_dir.exists():
        return
    runtime_tag = get_runtime_script_tag()
    for html_path in published_dir.rglob("*.html"):
        raw = html_path.read_text(encoding="utf-8")
        cleaned = _strip_tailwind_cdn(_strip_runtime_script(raw))
        body_html = strip_script_tags(extract_body_content(cleaned))
        styles = build_inline_styles(body_html)
        updated = cleaned
        if styles:
            updated = _insert_after_head(updated, styles)
        updated = _insert_before_body_end(updated, runtime_tag)
        if updated != raw:
            html_path.write_text(updated, encoding="utf-8")


def main() -> None:
    asyncio.run(_migrate_db())
    _migrate_published_files()


if __name__ == "__main__":
    main()
