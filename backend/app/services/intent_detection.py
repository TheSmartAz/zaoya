"""Intent detection for interview initialization."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
import json
import os
import re

from pydantic import BaseModel

from app.services.ai_service import (
    generate_response,
    resolve_available_model,
    DEFAULT_MODEL,
    is_model_available,
)


class IntentCategory(str, Enum):
    EVENT_INVITATION = "event-invitation"
    LANDING_PAGE = "landing-page"
    PORTFOLIO = "portfolio"
    CONTACT_FORM = "contact-form"
    ECOMMERCE = "ecommerce"
    BLOG = "blog"
    DASHBOARD = "dashboard"
    OTHER = "other"


class DetectedIntent(BaseModel):
    category: IntentCategory
    confidence: float
    inferred_fields: Dict[str, str]
    suggested_questions: List[str]


INTENT_PATTERNS: Dict[IntentCategory, Dict[str, List[str]]] = {
    IntentCategory.EVENT_INVITATION: {
        "keywords": [
            "wedding",
            "birthday",
            "party",
            "rsvp",
            "invitation",
            "invite",
            "event",
            "ceremony",
            "celebration",
        ],
        "questions": [
            "What's the date of the event?",
            "What time does it start?",
            "Where will it be held?",
            "What's the RSVP deadline?",
        ],
    },
    IntentCategory.LANDING_PAGE: {
        "keywords": [
            "landing",
            "launch",
            "marketing",
            "campaign",
            "product page",
            "waitlist",
            "signup",
        ],
        "questions": [
            "What's the main value proposition?",
            "Who's your target audience?",
            "What's the primary CTA?",
        ],
    },
    IntentCategory.PORTFOLIO: {
        "keywords": [
            "portfolio",
            "about me",
            "resume",
            "cv",
            "personal site",
            "profile",
        ],
        "questions": [
            "What's your name or brand?",
            "What projects should be highlighted?",
            "Any social links to include?",
        ],
    },
    IntentCategory.CONTACT_FORM: {
        "keywords": [
            "contact form",
            "contact",
            "get in touch",
            "inquiry",
            "lead form",
        ],
        "questions": [
            "What information should the form collect?",
            "Who should receive submissions?",
        ],
    },
    IntentCategory.ECOMMERCE: {
        "keywords": [
            "ecommerce",
            "e-commerce",
            "shop",
            "store",
            "cart",
            "checkout",
            "product catalog",
        ],
        "questions": [
            "What products or categories should be featured?",
            "Do you need a cart or checkout flow?",
        ],
    },
    IntentCategory.BLOG: {
        "keywords": [
            "blog",
            "newsletter",
            "articles",
            "posts",
            "writing",
        ],
        "questions": [
            "What topics will you write about?",
            "How should readers subscribe or follow?",
        ],
    },
    IntentCategory.DASHBOARD: {
        "keywords": [
            "dashboard",
            "analytics",
            "admin",
            "metrics",
            "reporting",
            "insights",
        ],
        "questions": [
            "Which metrics should be front and center?",
            "Any roles or permissions to consider?",
        ],
    },
}

INTENT_DEFAULT_FIELDS: Dict[IntentCategory, Dict[str, str]] = {
    IntentCategory.EVENT_INVITATION: {
        "scope.type": "event_invitation",
        "project_type": "Event invitation",
    },
    IntentCategory.LANDING_PAGE: {
        "scope.type": "landing_page",
        "project_type": "Landing page",
    },
    IntentCategory.PORTFOLIO: {
        "scope.type": "portfolio",
        "project_type": "Portfolio",
    },
    IntentCategory.CONTACT_FORM: {
        "scope.type": "contact_form",
        "project_type": "Contact form",
    },
    IntentCategory.ECOMMERCE: {
        "scope.type": "ecommerce",
        "project_type": "E-commerce",
    },
    IntentCategory.BLOG: {
        "scope.type": "blog",
        "project_type": "Blog",
    },
    IntentCategory.DASHBOARD: {
        "scope.type": "dashboard",
        "project_type": "Dashboard",
    },
}

INTENT_SYSTEM_PROMPT = """
You are an intent classifier for a website builder.

Return ONLY valid JSON with keys:
- category: one of [event-invitation, landing-page, portfolio, contact-form, ecommerce, blog, dashboard, other]
- confidence: float between 0 and 1
- inferred_fields: object with any inferred values. Use dotted keys where possible, e.g.
  - project_type
  - scope.type
  - timing.date
  - timing.time
  - timing.location
  - timing.rsvp_deadline
- suggested_questions: array of up to 4 short questions to ask next.

If unsure, choose category "other" with low confidence and generic questions.
""".strip()


async def detect_intent(message: str) -> DetectedIntent:
    """Detect user intent from the initial message."""
    message = message or ""
    if _should_use_ai():
        detected = await _detect_intent_with_ai(message)
        if detected:
            return detected
    return _detect_intent_keyword(message)


def get_intent_suggested_questions(category: IntentCategory) -> List[str]:
    return list(INTENT_PATTERNS.get(category, {}).get("questions", []))


def _should_use_ai() -> bool:
    if os.getenv("ZAOYA_DISABLE_INTENT_AI") == "1":
        return False
    if os.getenv("ZAOYA_INTENT_AI") == "0":
        return False
    model_id = resolve_available_model(os.getenv("ZAOYA_INTENT_MODEL", DEFAULT_MODEL))
    return is_model_available(model_id)


def _resolve_intent_model() -> str:
    preferred = os.getenv("ZAOYA_INTENT_MODEL", DEFAULT_MODEL)
    return resolve_available_model(preferred)


def _sanitize_detected_intent(payload: dict) -> Optional[DetectedIntent]:
    if not isinstance(payload, dict):
        return None
    payload.setdefault("confidence", 0.4)
    payload.setdefault("inferred_fields", {})
    payload.setdefault("suggested_questions", [])
    try:
        result = DetectedIntent.model_validate(payload)
    except Exception:
        return None

    confidence = max(0.0, min(float(result.confidence or 0.0), 1.0))
    result.confidence = confidence
    if not isinstance(result.inferred_fields, dict):
        result.inferred_fields = {}
    if not isinstance(result.suggested_questions, list):
        result.suggested_questions = []
    return result


def _extract_json(text: str) -> Optional[str]:
    if not text:
        return None
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced[0]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return None


async def _detect_intent_with_ai(message: str) -> Optional[DetectedIntent]:
    try:
        response_text = await generate_response(
            messages=[{"role": "user", "content": message}],
            model=_resolve_intent_model(),
            system_prompt=INTENT_SYSTEM_PROMPT,
            temperature=0.0,
        )
    except Exception:
        return None

    payload_text = _extract_json(response_text)
    if not payload_text:
        return None
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        return None

    return _sanitize_detected_intent(payload)


def _detect_intent_keyword(message: str) -> DetectedIntent:
    message = message or ""
    message_lower = message.lower()

    best_match: Optional[IntentCategory] = None
    best_score = 0.0

    for category, data in INTENT_PATTERNS.items():
        keywords = data.get("keywords", [])
        matches = sum(1 for kw in keywords if kw in message_lower)
        if matches <= 0:
            continue
        score = matches * 0.25
        if score > best_score:
            best_score = score
            best_match = category

    if not best_match:
        return DetectedIntent(
            category=IntentCategory.OTHER,
            confidence=0.3,
            inferred_fields={},
            suggested_questions=[
                "Can you tell me more about what you want to build?",
                "Who is this page for?",
                "What's the main goal?",
            ],
        )

    confidence = min(0.5 + best_score, 0.95)
    inferred_fields = _extract_fields(best_match, message)
    suggested_questions = list(INTENT_PATTERNS.get(best_match, {}).get("questions", []))

    return DetectedIntent(
        category=best_match,
        confidence=confidence,
        inferred_fields=inferred_fields,
        suggested_questions=suggested_questions,
    )


def _extract_fields(category: IntentCategory, message: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    defaults = INTENT_DEFAULT_FIELDS.get(category, {})
    fields.update(defaults)

    if category == IntentCategory.EVENT_INVITATION:
        fields.update(_extract_timing_fields(message))

    return fields


_DATE_PATTERNS = [
    r"\b(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?\b",
    r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
]

_TIME_PATTERN = r"\b\d{1,2}(?::\d{2})?\s?(?:am|pm)\b|\b\d{1,2}:\d{2}\b"


def _extract_timing_fields(message: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    date = _find_first_date(message)
    time = _find_first_time(message)
    location = _find_location(message)
    rsvp_deadline = _find_rsvp_deadline(message)

    if date:
        fields["timing.date"] = date
    if time:
        fields["timing.time"] = time
    if location:
        fields["timing.location"] = location
    if rsvp_deadline:
        fields["timing.rsvp_deadline"] = rsvp_deadline

    return fields


def _find_first_date(message: str) -> Optional[str]:
    for pattern in _DATE_PATTERNS:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def _find_first_time(message: str) -> Optional[str]:
    match = re.search(_TIME_PATTERN, message, re.IGNORECASE)
    if match:
        return match.group(0).strip()
    return None


def _find_location(message: str) -> Optional[str]:
    match = re.search(r"\b(?:at|in)\s+([^,.;\n]+)", message, re.IGNORECASE)
    if match:
        value = match.group(1).strip()
        if len(value) <= 80:
            return value
    return None


def _find_rsvp_deadline(message: str) -> Optional[str]:
    lower = message.lower()
    if "rsvp" not in lower:
        return None
    match = re.search(r"rsvp(?:\s+by|\s+before)?\s+([^,.;\n]+)", message, re.IGNORECASE)
    if match:
        candidate = match.group(1)
        date = _find_first_date(candidate)
        if date:
            return date
        time = _find_first_time(candidate)
        if time:
            return time
    return _find_first_date(message)
