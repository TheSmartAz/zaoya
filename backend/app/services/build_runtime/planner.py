"""Multi-page detection utilities for build runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import re


@dataclass
class MultiPageDecision:
    """Result of multi-page detection analysis."""

    is_multi_page: bool
    pages: List[str] = field(default_factory=list)
    reason: str = ""
    confidence: float = 0.0


@dataclass
class PageSpec:
    """Specification for a single page."""

    id: str
    name: str
    path: str
    description: str = ""
    is_main: bool = False
    sections: List[str] = field(default_factory=list)


class MultiPageDetector:
    """
    Detect if project needs multiple pages.

    Detection sources (priority order):
    1. ProductDoc page_plan (explicit)
    2. User message explicit request
    3. Content complexity analysis
    4. Project type inference
    """

    MULTI_SECTION_KEYWORDS = [
        "about",
        "features",
        "pricing",
        "contact",
        "blog",
        "team",
        "portfolio",
        "gallery",
        "testimonials",
        "services",
        "projects",
        "work",
        "faq",
        "careers",
    ]

    EXPLICIT_PATTERNS = [
        r"multiple pages?",
        r"several pages?",
        r"more than one page",
        r"homepage and",
        r"landing page and",
        r"\d+ pages?",
        r"多个页面",
        r"几个页面",
        r"多页",
        r"首页和",
    ]

    PROJECT_TYPE_PAGES = {
        "portfolio": [
            PageSpec("home", "Home", "/", "Portfolio home", True, ["hero", "featured_work"]),
            PageSpec("about", "About", "/about", "About me", False, ["bio", "skills"]),
            PageSpec("projects", "Projects", "/projects", "Work showcase", False, ["project_grid"]),
            PageSpec("contact", "Contact", "/contact", "Contact", False, ["contact_form"]),
        ],
        "business": [
            PageSpec("home", "Home", "/", "Business home", True, ["hero", "features"]),
            PageSpec("about", "About", "/about", "About us", False, ["company_intro"]),
            PageSpec("services", "Services", "/services", "Services", False, ["service_list"]),
            PageSpec("contact", "Contact", "/contact", "Contact", False, ["contact_form"]),
        ],
        "event": [
            PageSpec("home", "Home", "/", "Event home", True, ["hero", "event_details"]),
            PageSpec("rsvp", "RSVP", "/rsvp", "RSVP", False, ["rsvp_form"]),
            PageSpec("gallery", "Gallery", "/gallery", "Gallery", False, ["photo_gallery"]),
        ],
        "blog": [
            PageSpec("home", "Home", "/", "Blog home", True, ["hero", "recent_posts"]),
            PageSpec("posts", "Posts", "/posts", "Posts", False, ["post_list"]),
            PageSpec("about", "About", "/about", "About author", False, ["author_bio"]),
        ],
        "landing": [
            PageSpec("home", "Home", "/", "Landing", True, ["hero", "features", "cta"]),
        ],
    }

    async def detect(
        self,
        product_doc: Optional[object],
        user_message: str,
        project_type: Optional[str] = None,
    ) -> MultiPageDecision:
        """
        Analyze project requirements and decide if multi-page is needed.
        """
        page_plan = _get_doc_attr(product_doc, "page_plan", {}) or {}
        pages = page_plan.get("pages") if isinstance(page_plan, dict) else None
        if isinstance(pages, list) and len(pages) > 1:
            return MultiPageDecision(
                is_multi_page=True,
                pages=[str(p.get("name", "")).strip() for p in pages if isinstance(p, dict)],
                reason="ProductDoc specifies multiple pages",
                confidence=1.0,
            )

        if self._has_explicit_request(user_message):
            pages = self._extract_page_names(user_message)
            return MultiPageDecision(
                is_multi_page=True,
                pages=pages or ["Home", "About", "Contact"],
                reason="User explicitly requested multiple pages",
                confidence=0.95,
            )

        content_structure = _get_doc_attr(product_doc, "content_structure", {}) or {}
        sections = content_structure.get("sections") if isinstance(content_structure, dict) else None
        if isinstance(sections, list) and len(sections) > 5:
            return MultiPageDecision(
                is_multi_page=True,
                pages=self._suggest_pages_from_sections(sections),
                reason=f"Content has {len(sections)} sections, splitting across pages",
                confidence=0.8,
            )

        if project_type:
            normalized = project_type.strip().lower().replace("_", "-")
            if normalized in {"landing-page", "landingpage"}:
                normalized = "landing"
            elif normalized in {"event-invitation", "event-invite", "invitation"}:
                normalized = "event"
            if normalized in self.PROJECT_TYPE_PAGES:
                type_pages = self.PROJECT_TYPE_PAGES[normalized]
                if len(type_pages) > 1:
                    return MultiPageDecision(
                        is_multi_page=True,
                        pages=[p.name for p in type_pages],
                        reason=f"Project type '{normalized}' typically has multiple pages",
                        confidence=0.7,
                    )

        return MultiPageDecision(
            is_multi_page=False,
            reason="No multi-page indicators detected",
            confidence=0.9,
        )

    def _has_explicit_request(self, message: str) -> bool:
        message_lower = message.lower()
        return any(re.search(pattern, message_lower) for pattern in self.EXPLICIT_PATTERNS)

    def _extract_page_names(self, message: str) -> Optional[List[str]]:
        pages = []
        for keyword in self.MULTI_SECTION_KEYWORDS:
            if keyword.lower() in message.lower():
                pages.append(keyword.title())
        return list(dict.fromkeys(pages)) if pages else None

    def _suggest_pages_from_sections(self, sections: List[dict]) -> List[str]:
        pages = ["Home"]
        low_priority = [s for s in sections if isinstance(s, dict) and s.get("priority") != "high"]
        if len(low_priority) > 2:
            for section in low_priority:
                name = str(section.get("name", "")).lower()
                if any(kw in name for kw in ["about", "team", "contact"]):
                    pages.append(section.get("name", "").title())
        return list(dict.fromkeys([p for p in pages if p]))

    def get_page_specs(
        self,
        decision: MultiPageDecision,
        product_doc: Optional[object],
        project_type: Optional[str] = None,
    ) -> List[PageSpec]:
        if not decision.is_multi_page:
            sections = []
            content_structure = _get_doc_attr(product_doc, "content_structure", {}) or {}
            if isinstance(content_structure, dict):
                sections = [
                    str(s.get("name", "")).strip()
                    for s in content_structure.get("sections", [])
                    if isinstance(s, dict)
                ]
            return [
                PageSpec(
                    id="home",
                    name="Home",
                    path="/",
                    description="Main page",
                    is_main=True,
                    sections=[s for s in sections if s],
                )
            ]

        page_plan = _get_doc_attr(product_doc, "page_plan", {}) or {}
        pages = page_plan.get("pages") if isinstance(page_plan, dict) else None
        if isinstance(pages, list) and pages:
            specs: List[PageSpec] = []
            for page in pages:
                if not isinstance(page, dict):
                    continue
                specs.append(
                    PageSpec(
                        id=_slugify(str(page.get("id") or page.get("name") or "page")),
                        name=str(page.get("name") or "Page").strip(),
                        path=_normalize_path(str(page.get("path") or "/").strip()),
                        description=str(page.get("description") or "").strip(),
                        is_main=bool(page.get("is_main")),
                        sections=[
                            str(item).strip()
                            for item in (page.get("sections") or [])
                            if str(item).strip()
                        ],
                    )
                )
            if specs:
                return specs

        if project_type:
            normalized = project_type.strip().lower()
            if normalized in self.PROJECT_TYPE_PAGES:
                return list(self.PROJECT_TYPE_PAGES[normalized])

        specs = []
        for idx, name in enumerate(decision.pages or ["Home"]):
            safe_name = str(name).strip() or "Page"
            slug = _slugify(safe_name)
            specs.append(
                PageSpec(
                    id=_slugify(safe_name),
                    name=safe_name,
                    path="/" if idx == 0 else f"/{slug}",
                    description=f"{safe_name} page",
                    is_main=idx == 0,
                    sections=[],
                )
            )
        return specs


def _get_doc_attr(doc: Optional[object], field: str, default):
    if doc is None:
        return default
    if isinstance(doc, dict):
        return doc.get(field, default)
    return getattr(doc, field, default)


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"^-+|-+$", "", value)
    return value or "page"


def _normalize_path(path: str) -> str:
    value = (path or "/").strip()
    if not value.startswith("/"):
        value = f"/{value}"
    return value or "/"
