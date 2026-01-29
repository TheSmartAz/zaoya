"""HTML template rendering helpers for preview and publish."""

from __future__ import annotations

import base64
import hashlib
import html as html_escape
import re
from pathlib import Path
from typing import Dict, Optional

from app.services.tailwind_service import generate_tailwind_css

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
PREVIEW_TEMPLATE = "preview_template.html"
PUBLISH_TEMPLATE = "publish_template.html"

_template_cache: Dict[str, str] = {}
_runtime_cache: Dict[str, str] | None = None

TEMPLATE_ALIASES = {
    "preview_template_v1": PREVIEW_TEMPLATE,
    "publish_template_v1": PUBLISH_TEMPLATE,
}


def _load_template(name: str) -> str:
    if name in _template_cache:
        return _template_cache[name]
    template_path = TEMPLATE_DIR / name
    content = template_path.read_text(encoding="utf-8")
    _template_cache[name] = content
    return content


def resolve_template_name(template_id: Optional[str], fallback: str) -> str:
    if not template_id:
        return fallback
    resolved = TEMPLATE_ALIASES.get(template_id, template_id)
    if resolved.endswith(".html"):
        return resolved
    return fallback


def _load_runtime_script() -> Dict[str, str]:
    global _runtime_cache
    if _runtime_cache is not None:
        return _runtime_cache

    candidates = [
        Path(__file__).resolve().parents[3] / "frontend" / "public" / "zaoya-runtime.js",
        Path(__file__).resolve().parents[3] / "frontend" / "dist" / "zaoya-runtime.js",
    ]
    content = ""
    for path in candidates:
        if path.exists():
            content = path.read_text(encoding="utf-8")
            break

    if not content:
        content = "window.Zaoya = { submitForm: () => {}, track: () => {}, toast: () => {}, navigate: () => {} };"

    # Normalize to stable content for hashing
    content = content.strip() + "\n"
    digest = hashlib.sha256(content.encode("utf-8")).digest()
    hash_b64 = base64.b64encode(digest).decode("utf-8")

    _runtime_cache = {
        "content": content,
        "hash": f"sha256-{hash_b64}",
        "tag": f"<script>{content}</script>",
    }
    return _runtime_cache


def get_runtime_script_tag() -> str:
    return _load_runtime_script()["tag"]


def get_runtime_script_hash() -> str:
    return _load_runtime_script()["hash"]


def _render_template(template_name: str, context: Dict[str, str]) -> str:
    template = _load_template(template_name)
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def _safe(text: Optional[str]) -> str:
    return html_escape.escape(text or "")


def strip_script_tags(html: str) -> str:
    if not html:
        return ""
    # Remove script tags defensively (generated HTML should not include scripts).
    cleaned = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
    return cleaned


def build_inline_styles(html_body: str, extra_css: str = "") -> str:
    body_source = html_body or ""
    tailwind_css = generate_tailwind_css(body_source) if body_source.strip() else ""
    combined = "\n".join(filter(None, [tailwind_css, extra_css]))
    if not combined.strip():
        return ""
    return f"<style>{combined}</style>"


def render_preview_document(
    *,
    body_html: str,
    title: str = "Zaoya Preview",
    styles: str = "",
    body_class: str = "antialiased",
    page_script_tag: str = "",
    template_name: str = PREVIEW_TEMPLATE,
) -> str:
    context = {
        "TITLE": _safe(title),
        "STYLES": styles,
        "BODY_CLASS": body_class,
        "PAGE_HTML": body_html,
        "RUNTIME_SCRIPT": get_runtime_script_tag(),
        "PAGE_SCRIPT_TAG": page_script_tag,
    }
    return _render_template(template_name, context)


def render_publish_document(
    *,
    body_html: str,
    title: str,
    description: str,
    og_image: str,
    og_url: str,
    canonical_url: str,
    public_id: str,
    api_base: str,
    styles: str,
    favicon_url: str,
    robots_content: str = "index, follow",
    body_class: str = "antialiased",
    page_script_tag: str = "",
    template_name: str = PUBLISH_TEMPLATE,
) -> str:
    context = {
        "TITLE": _safe(title),
        "DESCRIPTION": _safe(description),
        "OG_TITLE": _safe(title),
        "OG_DESCRIPTION": _safe(description),
        "OG_IMAGE": _safe(og_image),
        "OG_URL": _safe(og_url),
        "CANONICAL_URL": _safe(canonical_url),
        "PUBLIC_ID": _safe(public_id),
        "API_BASE": _safe(api_base),
        "FAVICON_URL": _safe(favicon_url),
        "ROBOTS": _safe(robots_content),
        "STYLES": styles,
        "BODY_CLASS": body_class,
        "PAGE_HTML": body_html,
        "RUNTIME_SCRIPT": get_runtime_script_tag(),
        "PAGE_SCRIPT_TAG": page_script_tag,
    }
    return _render_template(template_name, context)
