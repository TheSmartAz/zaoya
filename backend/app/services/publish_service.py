"""Static HTML publishing service for multi-page projects."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.db import Project, Snapshot, Page, User, CustomDomain, ProductDoc
from app.services.template_renderer import (
    PUBLISH_TEMPLATE,
    build_inline_styles,
    render_publish_document,
    resolve_template_name,
    strip_script_tags,
)
from app.services.validator import extract_body_content
from app.services.thumbnail_queue import thumbnail_queue


class PublishService:
    """Service for publishing static HTML files."""

    def __init__(self, db: AsyncSession):
        self.db = db
        # Published pages directory
        self.publish_dir = Path(__file__).parent.parent.parent / "published_pages"
        self.publish_dir.mkdir(exist_ok=True)

    async def publish_project(self, project_id: UUID, snapshot_id: UUID) -> Dict[str, str]:
        """Publish a project snapshot as static HTML files.

        Returns dict with public_id and URLs for each page.
        """
        # Get snapshot with pages
        result = await self.db.execute(
            select(Snapshot).where(Snapshot.id == snapshot_id)
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise ValueError("Snapshot not found")

        pages_result = await self.db.execute(
            select(Page)
            .where(Page.snapshot_id == snapshot_id)
            .order_by(Page.display_order)
        )
        pages = list(pages_result.scalars().all())

        if not pages:
            raise ValueError("No pages to publish")

        # Get project for public_id
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        product_doc_result = await self.db.execute(
            select(ProductDoc).where(ProductDoc.project_id == project.id)
        )
        product_doc = product_doc_result.scalar_one_or_none()

        # Use existing public_id or generate new one
        public_id = project.public_id or self._generate_public_id()

        # Lookup user for vanity URLs
        user_result = await self.db.execute(
            select(User).where(User.id == project.user_id)
        )
        user = user_result.scalar_one_or_none()

        vanity_path = None
        if user and user.username and project.slug:
            vanity_path = f"/u/{user.username}/{project.slug}"

        custom_domain = None
        custom_result = await self.db.execute(
            select(CustomDomain).where(CustomDomain.project_id == project.id)
        )
        custom_domain = custom_result.scalar_one_or_none()

        if custom_domain and custom_domain.verification_status in ("verified", "active"):
            domain_origin = f"https://{custom_domain.domain}"
            base_path = domain_origin
            pages_base = domain_origin
            canonical_base = ""
        else:
            base_path = vanity_path or f"/p/{public_id}"
            canonical_base = vanity_path or f"/p/{public_id}"
            pages_base = settings.pages_url.rstrip("/")
        api_base = settings.api_url.rstrip("/")

        # Create project directory
        project_dir = self.publish_dir / public_id
        project_dir.mkdir(exist_ok=True)

        # Render each page
        urls = {}
        for page in pages:
            url_path = "index.html" if page.is_home else f"{page.slug}/index.html"
            page_dir = project_dir
            if not page.is_home:
                page_dir = project_dir / page.slug
                page_dir.mkdir(exist_ok=True)

            html_content = self._render_page(
                snapshot=snapshot,
                page=page,
                pages=pages,
                project=project,
                product_doc=product_doc,
                base_path=base_path,
                canonical_base=canonical_base,
                pages_base=pages_base,
                api_base=api_base,
                public_id=public_id,
            )

            page_file_path = page_dir / "index.html"
            page_file_path.write_text(html_content, encoding="utf-8")

            if page.js:
                (page_dir / "page.js").write_text(page.js, encoding="utf-8")

            url_suffix = url_path.replace("/index.html", "")
            urls[page.slug] = f"{base_path}/{url_suffix}".rstrip("/")

        # Update project with published snapshot
        project.published_snapshot_id = snapshot_id
        project.public_id = public_id
        project.published_at = datetime.utcnow()
        project.status = "published"
        project.updated_at = datetime.utcnow()
        await self.db.commit()

        # Queue OG image generation (low priority) for published pages
        try:
            for page in pages:
                await thumbnail_queue.enqueue_og_image(
                    db=self.db,
                    project_id=project.id,
                    page_id=page.id,
                    delay_seconds=60,
                )
        except Exception:
            # Best-effort: do not block publish
            pass

        return {
            "public_id": public_id,
            "base_url": base_path,
            "urls": urls,
        }

    def _generate_public_id(self) -> str:
        """Generate a unique 8-character public ID."""
        import random
        chars = "abcdefghjkmnpqrstuvwxyz23456789"  # No confusing chars
        return "".join(random.choice(chars) for _ in range(8))

    def _render_page(
        self,
        snapshot: Snapshot,
        page: Page,
        pages: List[Page],
        project: Project,
        product_doc: ProductDoc | None,
        base_path: str,
        canonical_base: str,
        pages_base: str,
        api_base: str,
        public_id: str,
    ) -> str:
        """Render a single page as static HTML."""
        # Build navigation links
        nav_links = self._build_nav_links(pages, base_path, page.slug)

        # Build header
        header_html = self._build_header(snapshot, nav_links)

        # Build footer
        footer_html = self._build_footer(snapshot, nav_links)

        # Build CSS variables from design system
        design_css = self._build_design_css(snapshot.design_system or {})

        # Build page content
        page_content = page.html or "<div>Page content</div>"
        page_body = strip_script_tags(extract_body_content(page_content))

        page_path = "" if page.is_home else page.slug
        if canonical_base:
            canonical_url = f"{pages_base}{canonical_base}/{page_path}".rstrip("/")
        else:
            canonical_url = f"{pages_base}/{page_path}".rstrip("/")

        metadata = page.page_metadata if isinstance(page.page_metadata, dict) else {}
        metadata_description = metadata.get("summary") or metadata.get("description") or ""
        doc_overview = product_doc.overview if product_doc else ""

        description = (doc_overview or metadata_description or page.title or project.name or "Zaoya Page").strip()

        page_title = (page.title or project.name or "Zaoya Page").strip()
        if project.name and page.title and page.title.strip() != project.name.strip():
            title = f"{page.title.strip()} | {project.name.strip()}"
        else:
            title = page_title

        og_image = f"{pages_base}/og-image/{project.id}/{page.id}"
        og_url = canonical_url

        favicon_url = ""
        if isinstance(project.template_inputs, dict):
            favicon_url = (
                project.template_inputs.get("favicon")
                or project.template_inputs.get("favicon_url")
                or project.template_inputs.get("faviconUrl")
                or ""
            )
        if not favicon_url:
            favicon_url = f"{pages_base}/favicon.ico"

        safe_title = title
        safe_description = description

        body_html = (
            f"{header_html}\n"
            f'<main id="zaoya-content" class="min-h-screen">{page_body}</main>\n'
            f"{footer_html}"
        )

        styles = build_inline_styles(body_html, design_css)
        script_tag = f'<script src="./page.js" defer></script>' if page.js else ""

        template_name = resolve_template_name(
            (project.render_templates or {}).get("publish"),
            PUBLISH_TEMPLATE,
        )

        return render_publish_document(
            body_html=body_html,
            title=safe_title,
            description=safe_description,
            og_image=og_image,
            og_url=og_url,
            canonical_url=canonical_url,
            public_id=public_id,
            api_base=api_base,
            styles=styles,
            body_class="bg-white antialiased",
            page_script_tag=script_tag,
            favicon_url=favicon_url,
            robots_content="index, follow",
            template_name=template_name,
        )

    def _build_nav_links(self, pages: List[Page], base_path: str, current_slug: str) -> List[Dict]:
        """Build navigation links for all pages."""
        nav_items = []
        for p in sorted(pages, key=lambda x: x.display_order):
            url_path = "" if p.is_home else p.slug
            nav_items.append({
                "title": p.title,
                "slug": p.slug,
                "url": f"{base_path}/{url_path}".rstrip("/"),
                "is_active": p.slug == current_slug,
            })
        return nav_items

    def _build_header(self, snapshot: Snapshot, nav_links: List[Dict]) -> str:
        """Build the header HTML with navigation."""
        nav_config = snapshot.navigation or {}
        header_config = nav_config.get("header", {})

        if not header_config.get("enabled", True):
            return ""

        links_html = "\n".join([
            f'<a href="{link["url"]}" class="px-4 py-2 hover:bg-gray-100 {link["is_active"] and "font-semibold" or ""}">{link["title"]}</a>'
            for link in nav_links
        ])

        return f"""<header class="border-b sticky top-0 bg-white z-10">
  <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex justify-between h-16 items-center">
      <div class="flex items-center">
        <span class="font-bold text-xl">{header_config.get("title", "")}</span>
      </div>
      <div class="hidden md:flex space-x-4">
        {links_html}
      </div>
    </div>
  </nav>
</header>"""

    def _build_footer(self, snapshot: Snapshot, nav_links: List[Dict]) -> str:
        """Build the footer HTML."""
        nav_config = snapshot.navigation or {}
        footer_config = nav_config.get("footer", {})

        if not footer_config.get("enabled", True):
            return ""

        links_html = "\n".join([
            f'<a href="{link["url"]}" class="hover:underline">{link["title"]}</a>'
            for link in footer_config.get("links", [])
        ])

        return f"""<footer class="border-t mt-12 py-8">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex justify-between">
      <p>{footer_config.get("text", "")}</p>
      <div class="space-x-4">
        {links_html}
      </div>
    </div>
  </div>
</footer>"""

    def _build_design_css(self, design_system: Dict) -> str:
        """Build CSS variables from design system."""
        colors = design_system.get("colors", {})
        typography = design_system.get("typography", {})
        spacing = design_system.get("spacing", "comfortable")
        border_radius = design_system.get("border_radius", "medium")
        animation_level = design_system.get("animation_level", "subtle")

        css_vars = []
        for key, value in colors.items():
            css_vars.append(f"--color-{key}: {value};")

        heading = typography.get("heading", {})
        body = typography.get("body", {})
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
