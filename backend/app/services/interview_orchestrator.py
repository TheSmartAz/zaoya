"""Interview orchestrator for v2 adaptive interview flow."""

from __future__ import annotations

from datetime import datetime, timezone
import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.models.schemas.interview import (
    AgentCallout,
    BuildPlan,
    CollectedAnswer,
    InterviewAnswerPayload,
    InterviewState,
    InterviewStatus,
    InterviewComplexity,
    AskedQuestion,
    OrchestratorResponse,
    PageSpec,
    ProductDocument,
    ProductDocumentContent,
    ProductDocumentDesign,
    ProductDocumentMetadata,
    ProductDocumentOverview,
    ProductDocumentTiming,
    ProductDocumentContact,
    ProjectBrief,
    Question,
    QuestionGroup,
    QuestionOption,
    AskGroupAction,
    AskFollowupAction,
    FinishAction,
    HandleOfftopicAction,
    SuggestEarlyFinishAction,
)
from app.services.ai_service import (
    generate_response,
    resolve_available_model,
    DEFAULT_MODEL,
    is_model_available,
)
from app.services.intent_detection import (
    detect_intent,
    DetectedIntent,
    IntentCategory,
    get_intent_suggested_questions,
)


TOPIC_LABELS = {
    "product_scope": "Product Scope",
    "audience": "Audience",
    "goals": "Goals",
    "content": "Content",
    "design": "Design",
    "technical": "Technical",
    "constraints": "Constraints",
    "intent": "Project details",
}

logger = logging.getLogger(__name__)


def _summarize_next_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    next_action = payload.get("next_action") if isinstance(payload, dict) else None
    if not isinstance(next_action, dict):
        summary["next_action_type"] = None
        return summary

    action_type = next_action.get("type")
    summary["next_action_type"] = action_type
    summary["has_group"] = isinstance(next_action.get("group"), dict)

    if action_type == "ask_group":
        group = next_action.get("group")
        if isinstance(group, dict):
            summary["group_id"] = group.get("id")
            questions = group.get("questions")
            if isinstance(questions, list):
                summary["question_count"] = len(questions)
    elif action_type == "ask_followup":
        questions = next_action.get("questions")
        if isinstance(questions, list):
            summary["question_count"] = len(questions)

    return summary


def _log_orchestrator_event(event: str, data: Dict[str, Any]) -> None:
    payload = {"event": event, **data}
    message = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    if os.getenv("ZAOYA_LOG_INTERVIEW_LLM") == "1":
        logger.warning(message)
    else:
        logger.debug(message)


QUESTION_BANK: List[Dict[str, Any]] = [
    {
        "topic": "product_scope",
        "slot": "scope.type",
        "text": "What are you building?",
        "type": "single_select",
        "default_value": "landing_page",
        "options": [
            ("landing_page", "Landing page"),
            ("portfolio", "Portfolio"),
            ("event_invite", "Event invitation"),
            ("saas", "SaaS/product app"),
            ("ecommerce", "E-commerce"),
            ("other", "Other"),
        ],
    },
    {
        "topic": "product_scope",
        "slot": "scope.pages",
        "text": "Which pages should be included?",
        "type": "multi_select",
        "default_value": ["home", "about", "contact"],
        "options": [
            ("home", "Home"),
            ("about", "About"),
            ("pricing", "Pricing"),
            ("contact", "Contact"),
            ("faq", "FAQ"),
            ("dashboard", "Dashboard"),
        ],
    },
    {
        "topic": "product_scope",
        "slot": "scope.features",
        "text": "Which key features should we highlight?",
        "type": "multi_select",
        "default_value": ["cta"],
        "options": [
            ("cta", "Strong call-to-action"),
            ("testimonials", "Testimonials"),
            ("gallery", "Image gallery"),
            ("pricing_table", "Pricing table"),
            ("newsletter", "Newsletter signup"),
        ],
    },
    {
        "topic": "audience",
        "slot": "audience.who",
        "text": "Who is the primary audience?",
        "type": "text",
        "default_value": "General audience",
        "options": None,
    },
    {
        "topic": "audience",
        "slot": "audience.context",
        "text": "Any context we should consider for the audience?",
        "type": "text",
        "default_value": "General",
        "options": None,
    },
    {
        "topic": "audience",
        "slot": "audience.size",
        "text": "Roughly how large is the audience?",
        "type": "single_select",
        "default_value": "small",
        "options": [
            ("small", "Small (1-10)"),
            ("medium", "Medium (10-50)"),
            ("large", "Large (50+)"),
        ],
    },
    {
        "topic": "goals",
        "slot": "goals.primary_goal",
        "text": "What is the primary goal of this page?",
        "type": "single_select",
        "default_value": "inform",
        "options": [
            ("collect_leads", "Collect leads"),
            ("drive_sales", "Drive sales"),
            ("grow_signups", "Grow signups"),
            ("inform", "Inform users"),
            ("rsvp", "Collect RSVPs"),
        ],
    },
    {
        "topic": "goals",
        "slot": "goals.success_criteria",
        "text": "How will you measure success?",
        "type": "text",
        "default_value": "More sign-ups",
        "options": None,
    },
    {
        "topic": "goals",
        "slot": "goals.cta",
        "text": "Preferred call-to-action text?",
        "type": "text",
        "default_value": "Get started",
        "options": None,
    },
    {
        "topic": "content",
        "slot": "content.sections",
        "text": "Which sections should we include?",
        "type": "multi_select",
        "default_value": ["hero", "features", "faq"],
        "options": [
            ("hero", "Hero"),
            ("features", "Features"),
            ("pricing", "Pricing"),
            ("testimonials", "Testimonials"),
            ("faq", "FAQ"),
        ],
    },
    {
        "topic": "content",
        "slot": "content.assets.logo",
        "text": "Do you have a logo?",
        "type": "single_select",
        "default_value": "generate",
        "options": [
            ("upload", "Yes, I will upload"),
            ("generate", "Please generate one"),
            ("none", "No logo"),
        ],
    },
    {
        "topic": "content",
        "slot": "content.assets.images",
        "text": "What images should we include?",
        "type": "multi_select",
        "default_value": ["product"],
        "options": [
            ("product", "Product screenshots"),
            ("team", "Team photos"),
            ("lifestyle", "Lifestyle imagery"),
            ("illustrations", "Illustrations"),
        ],
    },
    {
        "topic": "content",
        "slot": "content.assets.copy_text",
        "text": "Do you have copy ready?",
        "type": "single_select",
        "default_value": "tbd",
        "options": [
            ("ready", "Yes, I'll provide copy"),
            ("tbd", "Not yet"),
            ("generate", "Generate copy for me"),
        ],
    },
    {
        "topic": "design",
        "slot": "design.style",
        "text": "What style should it feel like?",
        "type": "single_select",
        "default_value": "modern",
        "options": [
            ("modern", "Modern"),
            ("playful", "Playful"),
            ("minimal", "Minimal"),
            ("luxury", "Luxury"),
            ("bold", "Bold"),
        ],
    },
    {
        "topic": "design",
        "slot": "design.mood",
        "text": "Any mood or vibe preferences?",
        "type": "single_select",
        "default_value": "friendly",
        "options": [
            ("friendly", "Friendly"),
            ("professional", "Professional"),
            ("playful", "Playful"),
            ("premium", "Premium"),
        ],
    },
    {
        "topic": "design",
        "slot": "design.colors",
        "text": "Any color preferences?",
        "type": "multi_select",
        "default_value": ["neutral"],
        "options": [
            ("blue", "Blue"),
            ("neutral", "Neutral"),
            ("pastel", "Pastel"),
            ("vibrant", "Vibrant"),
            ("dark", "Dark"),
        ],
    },
    {
        "topic": "technical",
        "slot": "technical.auth_required",
        "text": "Do you need user authentication?",
        "type": "single_select",
        "default_value": "no",
        "options": [
            ("yes", "Yes, required"),
            ("optional", "Optional"),
            ("no", "No"),
        ],
    },
    {
        "topic": "technical",
        "slot": "technical.integrations",
        "text": "Any integrations needed?",
        "type": "multi_select",
        "default_value": [],
        "options": [
            ("stripe", "Payments (Stripe)"),
            ("analytics", "Analytics"),
            ("email", "Email"),
            ("social_login", "Social login"),
        ],
    },
    {
        "topic": "constraints",
        "slot": "technical.constraints",
        "text": "Any constraints or requirements we should know?",
        "type": "text",
        "default_value": "None",
        "options": None,
    },
]

INTENT_PRIORITY_SLOTS: Dict[str, List[str]] = {
    IntentCategory.EVENT_INVITATION.value: [
        "timing.date",
        "timing.location",
        "timing.time",
        "timing.rsvp_deadline",
        "goals.primary_goal",
    ],
    IntentCategory.LANDING_PAGE.value: [
        "goals.primary_goal",
        "goals.cta",
        "audience.who",
    ],
    IntentCategory.PORTFOLIO.value: [
        "scope.pages",
        "content.sections",
        "design.style",
    ],
    IntentCategory.CONTACT_FORM.value: [
        "scope.features",
        "technical.integrations",
        "goals.primary_goal",
    ],
    IntentCategory.ECOMMERCE.value: [
        "scope.features",
        "content.sections",
        "technical.integrations",
    ],
    IntentCategory.BLOG.value: [
        "content.sections",
        "audience.who",
        "design.style",
    ],
    IntentCategory.DASHBOARD.value: [
        "scope.features",
        "technical.auth_required",
        "technical.integrations",
    ],
}

ORCHESTRATOR_SYSTEM_PROMPT = """
You are an interview orchestrator for Zaoya, an AI website builder.

You have access to three specialist perspectives:
- RequirementsAgent: extract requirements, constraints, goals
- UXAgent: reduce ambiguity with the fewest questions
- TechAgent: flag technical constraints and risks

Given the user's message and current interview state:
1) Extract new info into brief_patch
2) Decide next_action (ask_group, ask_followup, finish, handle_offtopic, suggest_early_finish)
3) Generate agent_callouts for UI
4) Assess user_sentiment

Rules:
- Group related questions (max 3 per group) by topic
- Every question must include: id, text, type, slot, options (list of {value,label}), and allow_other true
- Use single_select or multi_select for choice questions
- Use text/date for free-form, but still include suggested options when helpful
- Do not ask for info already present in the brief
- Keep question count adaptive to complexity
- If user is impatient or asks to generate, suggest early finish

Output ONLY valid JSON matching this schema:
{
  "mode": "interview|off_topic|finish",
  "agent_callouts": [{"agent":"RequirementsAgent|UXAgent|TechAgent|PlannerAgent","content":"..."}],
  "brief_patch": { ...Partial<ProjectBrief>... },
  "next_action": {
    "type": "ask_group|ask_followup|finish|handle_offtopic|suggest_early_finish",
    ...
  },
  "confidence": 0.0-1.0,
  "reason_codes": ["..."],
  "user_sentiment": "engaged|neutral|impatient|frustrated"
}
""".strip()

PRODUCT_DOCUMENT_SYSTEM_PROMPT = """
You are a product document generator for Zaoya.
Given a structured ProjectBrief, create a ProductDocument JSON object.
Follow this schema exactly and respond with JSON only:
{
  "project_type": "string",
  "overview": {
    "name": "string",
    "description": "string",
    "target_audience": "string"
  },
  "timing": {
    "date": "string",
    "time": "string",
    "duration": "string",
    "location": "string"
  },
  "design": {
    "theme": "string",
    "color_palette": ["#hex", ...],
    "style_keywords": ["string", ...]
  },
  "content": {
    "sections": ["string", ...],
    "features": ["string", ...],
    "requirements": ["string", ...]
  },
  "contact": {
    "methods": ["string", ...],
    "info": "string"
  },
  "metadata": {
    "created_at": 0,
    "interview_duration": 0,
    "questions_asked": 0,
    "questions_skipped": 0
  }
}
If timing or contact is unknown, omit those fields (do not invent).
If questions_skipped > 0, include a requirement in content.requirements noting defaults were applied.
""".strip()

BUILD_PLAN_EDIT_SYSTEM_PROMPT = """
You are a build plan editor for Zaoya.
Given an existing BuildPlan and a user instruction, update the plan accordingly.

Rules:
- Return ONLY valid JSON matching the BuildPlan schema.
- Preserve existing page IDs/paths when possible.
- If adding a page, create a unique id and path.
- Keep fields you are not asked to change as-is.

BuildPlan schema:
{
  "pages": [
    {"id": "string", "name": "string", "path": "string", "sections": ["string"], "is_main": false}
  ],
  "design_system": {},
  "features": ["string"],
  "estimated_complexity": "low|medium|high"
}
""".strip()


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _detect_language(text: str) -> str:
    if not text:
        return "en"
    # Basic CJK detection
    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            return "zh"
    return "en"


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"^-+|-+$", "", value)
    return value or "page"


def _deep_merge(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base.get(key, {}), value)
        else:
            base[key] = value
    return base


def _should_use_ai() -> bool:
    if os.getenv("ZAOYA_DISABLE_INTERVIEW_AI") == "1":
        return False
    if os.getenv("ZAOYA_INTERVIEW_AI") == "1":
        return True
    # Default to AI when a model key is available
    return True


def analyze_complexity(text: str) -> str:
    if not text:
        return "medium"

    lowered = text.lower()
    high_keywords = [
        "saas",
        "dashboard",
        "platform",
        "subscription",
        "pricing",
        "authentication",
        "multi-page",
        "workflow",
        "admin",
        "crm",
        "marketplace",
    ]
    low_keywords = [
        "invitation",
        "birthday",
        "wedding",
        "party",
        "poster",
        "flyer",
        "simple",
        "single page",
        "landing",
    ]

    if any(k in lowered for k in high_keywords) or len(text) > 220:
        return "high"
    if any(k in lowered for k in low_keywords) and len(text) < 140:
        return "low"
    return "medium"


def _target_question_count(complexity: str) -> int:
    if complexity == "low":
        return 3
    if complexity == "high":
        return 15
    return 8


def _parse_intent_category(value: Optional[str]) -> Optional[IntentCategory]:
    if not value:
        return None
    try:
        return IntentCategory(value)
    except ValueError:
        return None


def _suggested_questions_for_state(state: InterviewState) -> Optional[List[str]]:
    category = _parse_intent_category(state.detected_intent)
    if not category:
        return None
    questions = get_intent_suggested_questions(category)
    return questions or None


def _apply_intent_fields(
    brief: ProjectBrief,
    inferred_fields: Dict[str, str],
    allow_overwrite: bool = False,
) -> None:
    if not inferred_fields:
        return
    for slot, value in inferred_fields.items():
        if value in (None, ""):
            continue
        current = _get_brief_value(brief, slot)
        if not allow_overwrite and current not in (None, "", []):
            continue
        _set_brief_value(brief, slot, value)


def _build_intent_question_defs(
    brief: ProjectBrief,
    suggested_questions: List[str],
) -> List[Dict[str, Any]]:
    if not suggested_questions:
        return []
    intent_questions: List[Dict[str, Any]] = []
    seen_slots: set[str] = set()
    for text in suggested_questions:
        payload = {"id": text[:16], "text": text}
        slot = _infer_slot(payload)
        if not slot or slot in seen_slots:
            continue
        if not _is_valid_slot(brief, slot):
            continue
        if _get_brief_value(brief, slot) not in (None, "", []):
            continue
        question_type = "date" if slot == "timing.date" else "text"
        intent_questions.append(
            {
                "topic": "intent",
                "slot": slot,
                "text": text,
                "type": question_type,
                "default_value": None,
                "options": None,
            }
        )
        seen_slots.add(slot)
    return intent_questions


def _prioritize_question_defs(
    questions: List[Dict[str, Any]],
    priority_slots: List[str],
) -> List[Dict[str, Any]]:
    if not priority_slots:
        return questions
    order = {slot: idx for idx, slot in enumerate(priority_slots)}
    return sorted(
        questions,
        key=lambda item: order.get(item.get("slot"), len(order)),
    )


def _format_known_facts(brief: ProjectBrief) -> str:
    return json.dumps(brief.model_dump(), ensure_ascii=False, indent=2)


def _format_answers_for_prompt(
    state: InterviewState,
    user_message: Optional[str],
    answers: List[InterviewAnswerPayload],
) -> str:
    parts = []
    if user_message:
        parts.append(f'User message: "{user_message}"')

    if answers:
        question_lookup: Dict[str, Question] = {}
        for group in state.question_plan:
            for question in group.questions:
                question_lookup[question.id] = question
        for answer in answers:
            question = question_lookup.get(answer.question_id)
            label = question.text if question else answer.question_id
            parts.append(
                f"- {label}: selected={answer.selected_options or []}, text={answer.raw_text or ''}"
            )

    return "\n".join(parts) if parts else "(no user input)"


def _build_orchestrator_prompt(
    state: InterviewState,
    user_message: Optional[str],
    answers: List[InterviewAnswerPayload],
    action: str,
) -> str:
    payload = _format_answers_for_prompt(state, user_message, answers)
    suggested_questions = _suggested_questions_for_state(state) or []
    return f"""
CURRENT_STATE:
status: {state.status}
complexity: {state.complexity}
detected_intent: {state.detected_intent}
intent_confidence: {state.confidence}
current_group_index: {state.current_group_index}
question_plan: {json.dumps([g.model_dump() for g in state.question_plan], ensure_ascii=False)}
suggested_questions: {json.dumps(suggested_questions, ensure_ascii=False)}
asked_count: {len(state.asked)}
answers_count: {len(state.answers)}
brief: {_format_known_facts(state.brief)}

USER_ACTION: {action}
USER_INPUT:
{payload}

Return the OrchestratorResponse JSON.
""".strip()


def _build_question(option: Dict[str, Any]) -> Question:
    options = None
    if option.get("options"):
        options = [
            QuestionOption(value=value, label=label)
            for value, label in option["options"]
        ]
    elif option.get("type") in {"text", "date"}:
        options = [
            QuestionOption(value="not_sure", label="Not sure"),
            QuestionOption(value="skip", label="Skip this"),
        ]
    return Question(
        id=f"q_{uuid4().hex[:8]}",
        text=option["text"],
        type=option["type"],
        options=options,
        allow_other=True,
        slot=option["slot"],
        default_value=option.get("default_value"),
    )


def _resolve_interview_model(preferred: Optional[str] = None) -> Optional[str]:
    if os.getenv("ZAOYA_INTERVIEW_MOCK") == "1":
        return "mock"
    interview_model = os.getenv("ZAOYA_INTERVIEW_MODEL")
    if interview_model:
        preferred_value = interview_model
    else:
        preferred_value = preferred or DEFAULT_MODEL
    model_id = resolve_available_model(preferred_value)
    if not is_model_available(model_id):
        return None
    return model_id


def _get_brief_value(brief: ProjectBrief, slot: str) -> Any:
    current: Any = brief
    for part in slot.split("."):
        current = getattr(current, part, None)
        if current is None:
            return None
    return current


def _set_brief_value(brief: ProjectBrief, slot: str, value: Any) -> None:
    parts = slot.split(".")
    target: Any = brief
    for part in parts[:-1]:
        try:
            target = getattr(target, part)
        except AttributeError:
            return
    attr = parts[-1]
    try:
        current_value = getattr(target, attr)
    except AttributeError:
        return
    if isinstance(current_value, list):
        if isinstance(value, list):
            setattr(target, attr, value)
        elif value is None:
            return
        else:
            setattr(target, attr, [value])
    else:
        setattr(target, attr, value)


def apply_brief_patch(brief: ProjectBrief, patch: Dict[str, Any]) -> ProjectBrief:
    if not patch:
        return brief

    # Handle dotted keys
    dotted = {k: v for k, v in patch.items() if "." in k}
    for key, value in dotted.items():
        _set_brief_value(brief, key, value)

    # Handle nested patch
    nested_patch = {k: v for k, v in patch.items() if "." not in k}
    if nested_patch:
        brief_dict = brief.model_dump()
        allowed = set(brief_dict.keys())
        safe_patch = {k: v for k, v in nested_patch.items() if k in allowed}
        merged = _deep_merge(brief_dict, safe_patch)
        brief = ProjectBrief.model_validate(merged)

    return brief


def _normalize_answer(question: Question, answer: InterviewAnswerPayload) -> Dict[str, Any]:
    raw = (answer.raw_text or "").strip()
    selected = answer.selected_options or []
    extracted: Dict[str, Any] = {}

    if question.slot == "technical.auth_required":
        text = raw.lower()
        if selected:
            text = selected[0].lower()
        if "yes" in text or "required" in text:
            extracted[question.slot] = True
        elif "no" in text:
            extracted[question.slot] = False
        else:
            extracted[question.slot] = None
        return extracted

    if question.type == "multi_select":
        if selected:
            extracted[question.slot] = selected
        elif raw:
            extracted[question.slot] = [item.strip() for item in raw.split(",") if item.strip()]
        return extracted

    if question.type == "single_select":
        if selected:
            extracted[question.slot] = selected[0]
        elif raw:
            extracted[question.slot] = raw
        return extracted

    if raw:
        extracted[question.slot] = raw
    return extracted


def _is_nonempty_answer(answer: InterviewAnswerPayload) -> bool:
    if answer.selected_options:
        return True
    return bool((answer.raw_text or "").strip())


def _generate_questions(
    intent: DetectedIntent,
    brief: ProjectBrief,
    complexity: str,
) -> List[QuestionGroup]:
    """Generate question groups based on detected intent."""
    return generate_question_plan(
        brief,
        complexity,
        detected_intent=intent.category.value,
        suggested_questions=intent.suggested_questions,
    )


def generate_question_plan(
    brief: ProjectBrief,
    complexity: str,
    detected_intent: Optional[str] = None,
    suggested_questions: Optional[List[str]] = None,
) -> List[QuestionGroup]:
    intent_questions: List[Dict[str, Any]] = []
    intent_slots: set[str] = set()

    intent_category = _parse_intent_category(detected_intent)
    if intent_category and not suggested_questions:
        suggested_questions = get_intent_suggested_questions(intent_category)

    if suggested_questions:
        intent_questions = _build_intent_question_defs(brief, suggested_questions)
        intent_slots = {q["slot"] for q in intent_questions}

    missing_questions = []
    for option in QUESTION_BANK:
        if option["slot"] in intent_slots:
            continue
        if _get_brief_value(brief, option["slot"]) in (None, [], ""):
            missing_questions.append(option)

    priority_slots = INTENT_PRIORITY_SLOTS.get(detected_intent or "", [])
    missing_questions = _prioritize_question_defs(missing_questions, priority_slots)

    target = _target_question_count(complexity)
    selected: List[Dict[str, Any]] = []
    if intent_questions:
        selected.extend(intent_questions[:target])
    remaining = max(target - len(selected), 0)
    if remaining:
        selected.extend(missing_questions[:remaining])

    grouped: Dict[str, List[Question]] = {}
    for option in selected:
        group = grouped.setdefault(option["topic"], [])
        if len(group) >= 3:
            continue
        group.append(_build_question(option))

    question_groups = []
    for topic, questions in grouped.items():
        question_groups.append(
            QuestionGroup(
                id=f"grp_{uuid4().hex[:8]}",
                topic=topic,
                topic_label=TOPIC_LABELS.get(topic, topic.title()),
                questions=questions,
                is_completed=False,
            )
        )

    return question_groups


def _extract_json(text: str) -> str:
    if not text:
        return "{}"
    # Strip code fences if present
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced[0]
    # Fallback: take first JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return "{}"


def _fill_orchestrator_defaults(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload.setdefault("agent_callouts", [])
    payload.setdefault("brief_patch", {})
    payload.setdefault("confidence", 0.5)
    payload.setdefault("reason_codes", ["repaired_payload"])
    payload.setdefault("user_sentiment", "neutral")
    return payload


SLOT_ALIASES = {
    "primary_goal": "goals.primary_goal",
    "goal": "goals.primary_goal",
    "goals": "goals.primary_goal",
    "design_style": "design.style",
    "visual_style": "design.style",
    "style": "design.style",
    "vibe_mood": "design.mood",
    "mood": "design.mood",
    "target_audience": "audience.who",
    "audience_who": "audience.who",
    "audience": "audience.who",
    "key_features": "scope.features",
    "features": "scope.features",
    "pages": "scope.pages",
    "cta": "goals.cta",
    "content_sections": "content.sections",
    "copy": "content.assets.copy_text",
    "copy_text": "content.assets.copy_text",
    "integrations": "technical.integrations",
    "constraints": "technical.constraints",
    "rsvp_method": "scope.features",
    "rsvp_fields": "scope.features",
    "hero_image_source": "content.assets.images",
    "hero_image": "content.assets.images",
    "event_date": "timing.date",
    "event_time": "timing.time",
    "event_location": "timing.location",
    "rsvp_deadline": "timing.rsvp_deadline",
}


def _infer_slot(question: Dict[str, Any]) -> Optional[str]:
    qid = str(question.get("id") or "").lower()
    if qid in SLOT_ALIASES:
        return SLOT_ALIASES[qid]

    text = str(question.get("text") or "").lower()
    if "audience" in text:
        return "audience.who"
    if "value proposition" in text:
        return "goals.primary_goal"
    if "cta" in text or "call-to-action" in text:
        return "goals.cta"
    if "goal" in text:
        return "goals.primary_goal"
    if "name" in text or "brand" in text or "bio" in text:
        return "content.assets.copy_text"
    if "style" in text or "vibe" in text or "mood" in text:
        return "design.style"
    if "feature" in text:
        return "scope.features"
    if "project" in text or "workflow" in text:
        return "scope.features"
    if "page" in text:
        return "scope.pages"
    if "product" in text or "category" in text:
        return "scope.features"
    if "topic" in text:
        return "content.sections"
    if "integration" in text:
        return "technical.integrations"
    if "subscribe" in text or "newsletter" in text or "follow" in text:
        return "technical.integrations"
    if "role" in text or "permission" in text:
        return "technical.constraints"
    if "form" in text or "field" in text:
        return "scope.features"
    if "constraint" in text or "requirement" in text:
        return "technical.constraints"
    if "date" in text or "when" in text:
        return "timing.date"
    if "time" in text:
        return "timing.time"
    if "location" in text or "where" in text or "venue" in text:
        return "timing.location"
    if "deadline" in text:
        return "timing.rsvp_deadline"
    if "rsvp" in text:
        if "by" in text or "before" in text:
            return "timing.rsvp_deadline"
        return "scope.features"
    if "social" in text or "links" in text:
        return "technical.integrations"
    if "photo" in text or "image" in text:
        return "content.assets.images"
    return None


def _is_valid_slot(brief: ProjectBrief, slot: str) -> bool:
    try:
        current: Any = brief
        for part in slot.split("."):
            if not hasattr(current, part):
                return False
            current = getattr(current, part)
        return True
    except AttributeError:
        return False


def _normalize_question_payloads(
    questions: List[Dict[str, Any]],
    brief: ProjectBrief,
) -> Optional[List[Dict[str, Any]]]:
    normalized: List[Dict[str, Any]] = []
    for question in questions:
        if not isinstance(question, dict):
            return None
        q = dict(question)
        if not q.get("id"):
            q["id"] = f"q_{uuid4().hex[:8]}"
        if not q.get("type"):
            q["type"] = "text"
        if not q.get("text"):
            return None
        if "slot" not in q or not q.get("slot"):
            inferred = _infer_slot(q)
            if not inferred:
                return None
            q["slot"] = inferred
        elif not _is_valid_slot(brief, q["slot"]):
            inferred = _infer_slot(q)
            if not inferred:
                last_part = str(q["slot"]).split(".")[-1]
                inferred = SLOT_ALIASES.get(last_part)
            if inferred and _is_valid_slot(brief, inferred):
                q["slot"] = inferred
            else:
                return None
        if "allow_other" not in q:
            q["allow_other"] = True

        options = q.get("options")
        if isinstance(options, list) and options:
            if all(isinstance(opt, str) for opt in options):
                q["options"] = [
                    {"value": opt, "label": opt} for opt in options if str(opt).strip()
                ]
            elif all(isinstance(opt, dict) for opt in options):
                cleaned = []
                for opt in options:
                    value = opt.get("value") or opt.get("label")
                    label = opt.get("label") or opt.get("value")
                    if not value or not label:
                        continue
                    cleaned.append(
                        {
                            "value": value,
                            "label": label,
                            "description": opt.get("description"),
                        }
                    )
                q["options"] = cleaned
        normalized.append(q)
    return normalized


def _repair_orchestrator_payload(
    payload_text: str,
    state: InterviewState,
) -> Optional[OrchestratorResponse]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    if isinstance(payload.get("orchestrator"), dict):
        payload = payload["orchestrator"]

    payload = _fill_orchestrator_defaults(payload)
    next_action = payload.get("next_action")
    if not isinstance(next_action, dict):
        return None

    action_type = next_action.get("type")
    if action_type == "finish":
        payload["mode"] = "finish"
    elif action_type == "handle_offtopic":
        payload["mode"] = "off_topic"
    else:
        payload["mode"] = "interview"
    if action_type == "ask_group" and not isinstance(next_action.get("group"), dict):
        questions: Optional[List[Dict[str, Any]]] = None
        if isinstance(next_action.get("questions"), list):
            questions = next_action.get("questions")
        elif isinstance(payload.get("questions"), list):
            questions = payload.get("questions")
        elif isinstance(payload.get("question_group"), dict):
            group_payload = payload.get("question_group")
            if isinstance(group_payload.get("questions"), list):
                next_action["group"] = group_payload

        if "group" not in next_action:
            if questions:
                normalized_questions = _normalize_question_payloads(questions, state.brief)
                if normalized_questions is None:
                    questions = None
                else:
                    questions = normalized_questions
                topic = next_action.get("topic") or payload.get("topic") or "general"
                topic_label = (
                    next_action.get("topic_label")
                    or payload.get("topic_label")
                    or TOPIC_LABELS.get(topic, topic.replace("_", " ").title())
                )
                if questions:
                    next_action["group"] = {
                        "id": f"grp_{uuid4().hex[:8]}",
                        "topic": topic,
                        "topic_label": topic_label,
                        "questions": questions,
                        "is_completed": False,
                    }
                    next_action.pop("questions", None)
                else:
                    return None

    if action_type == "ask_group" and isinstance(next_action.get("group"), dict):
        group_payload = next_action.get("group")
        if isinstance(group_payload, dict):
            questions = group_payload.get("questions")
            if isinstance(questions, list):
                normalized_questions = _normalize_question_payloads(questions, state.brief)
                if normalized_questions is None:
                    return None
                else:
                    group_payload["questions"] = normalized_questions

    if action_type == "ask_followup" and "questions" not in next_action:
        group_payload = next_action.get("group")
        if isinstance(group_payload, dict) and isinstance(group_payload.get("questions"), list):
            next_action["questions"] = group_payload["questions"]

    try:
        return OrchestratorResponse.model_validate(payload)
    except Exception:
        return None


async def _call_orchestrator_llm(
    state: InterviewState,
    user_message: Optional[str],
    answers: List[InterviewAnswerPayload],
    action: str,
    model_id: Optional[str] = None,
) -> OrchestratorResponse:
    model_id = model_id or _resolve_interview_model()
    if not model_id:
        raise RuntimeError("No available model for interview orchestrator")
    if model_id == "mock":
        return _mock_orchestrator_response(state, user_message, action)

    prompt = _build_orchestrator_prompt(state, user_message, answers, action)

    last_error: Optional[Exception] = None
    for attempt in range(3):
        payload_text = ""
        try:
            response_text = await generate_response(
                messages=[{"role": "user", "content": prompt}],
                model=model_id,
                system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            )
            payload_text = _extract_json(response_text)
            payload_summary: Dict[str, Any] = {}
            try:
                payload_summary = _summarize_next_action(json.loads(payload_text))
            except json.JSONDecodeError:
                payload_summary = {"next_action_type": None, "parse_error": "invalid_json"}
            _log_orchestrator_event(
                "interview_orchestrator_llm_response",
                {
                    "model_id": model_id,
                    "raw_response": response_text,
                    "payload_text": payload_text,
                    **payload_summary,
                },
            )
            try:
                payload_data = json.loads(payload_text)
            except json.JSONDecodeError:
                payload_data = {}
            if isinstance(payload_data, dict):
                next_action = payload_data.get("next_action")
                if (
                    isinstance(next_action, dict)
                    and next_action.get("type") == "finish"
                    and ("plan" not in next_action or "product_document" not in next_action)
                ):
                    _log_orchestrator_event(
                        "interview_orchestrator_finish_fallback",
                        {"model_id": model_id, "reason": "missing_plan_or_doc"},
                    )
                    return await finalize_interview(
                        state,
                        reason="llm_finish_missing_plan",
                        final_status="done",
                        model_id=model_id,
                    )
            return OrchestratorResponse.model_validate_json(payload_text)
        except Exception as exc:  # noqa: BLE001 - retry on any parse or API error
            last_error = exc
            if payload_text:
                repaired = _repair_orchestrator_payload(payload_text, state)
                if repaired:
                    payload_summary: Dict[str, Any] = {}
                    try:
                        payload_summary = _summarize_next_action(json.loads(payload_text))
                    except json.JSONDecodeError:
                        payload_summary = {"next_action_type": None, "parse_error": "invalid_json"}
                    _log_orchestrator_event(
                        "interview_orchestrator_payload_repaired",
                        {
                            "model_id": model_id,
                            "error": str(exc),
                            "payload_text": payload_text,
                            **payload_summary,
                        },
                    )
                    return repaired
            await asyncio.sleep(2 ** attempt)

    raise RuntimeError(f"Failed to generate orchestrator response: {last_error}")


def _mock_orchestrator_response(
    state: InterviewState,
    user_message: Optional[str],
    action: str,
) -> OrchestratorResponse:
    """Deterministic mock response used in tests to avoid external LLM calls."""
    question_text = "What's the primary goal for this experience?"
    question = Question(
        id=f"q_{uuid4().hex[:8]}",
        text=question_text,
        type="single_select",
        options=[
            QuestionOption(value="play", label="Play the game"),
            QuestionOption(value="learn", label="Learn more"),
            QuestionOption(value="other", label="Other"),
        ],
        allow_other=True,
        slot="goals.primary_goal",
        default_value=None,
    )
    group = QuestionGroup(
        id=f"grp_{uuid4().hex[:8]}",
        topic="intent",
        topic_label=TOPIC_LABELS.get("intent", "Project details"),
        questions=[question],
        is_completed=False,
    )
    return OrchestratorResponse(
        mode="interview",
        agent_callouts=_build_agent_callouts(),
        brief_patch={},
        next_action=AskGroupAction(type="ask_group", group=group),
        confidence=0.5,
        reason_codes=[f"mock:{action}"],
        user_sentiment="neutral",
    )


async def _generate_product_document(
    brief: ProjectBrief,
    plan: Optional[BuildPlan] = None,
    model_id: Optional[str] = None,
) -> ProductDocument:
    model_id = model_id or _resolve_interview_model()
    if not model_id:
        raise RuntimeError("No available model for product document")

    payload: Dict[str, Any] = {
        "brief": brief.model_dump(),
        "defaults_applied": brief.questions_skipped > 0,
    }
    if plan:
        payload["build_plan"] = plan.model_dump()
    prompt = f"Input JSON:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            response_text = await generate_response(
                messages=[{"role": "user", "content": prompt}],
                model=model_id,
                system_prompt=PRODUCT_DOCUMENT_SYSTEM_PROMPT,
            )
            payload_text = _extract_json(response_text)
            return ProductDocument.model_validate_json(payload_text)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            await asyncio.sleep(2 ** attempt)

    raise RuntimeError(f"Failed to generate product document: {last_error}")


def _fallback_product_document(
    brief: ProjectBrief,
    plan: Optional[BuildPlan] = None,
) -> ProductDocument:
    overview = ProductDocumentOverview(
        name=brief.project_type or brief.scope.type or "Project",
        description=brief.goals.primary_goal or "Generated page",
        target_audience=brief.audience.who or "General audience",
    )
    design = ProductDocumentDesign(
        theme=brief.design.style
        or (plan.design_system.get("style") if plan else None)
        or "modern",
        color_palette=brief.design.colors
        or (plan.design_system.get("colors") if plan else None)
        or [],
        style_keywords=[brief.design.mood] if brief.design.mood else [],
    )
    content = ProductDocumentContent(
        sections=brief.content.sections or [],
        features=plan.features if plan and plan.features else brief.scope.features or brief.technical.integrations or [],
        requirements=brief.technical.constraints or [],
    )
    timing = None
    if brief.timing and any(
        [brief.timing.date, brief.timing.time, brief.timing.location, brief.timing.rsvp_deadline]
    ):
        timing = ProductDocumentTiming(
            date=brief.timing.date or "TBD",
            time=brief.timing.time or "TBD",
            duration=None,
            location=brief.timing.location,
        )
    if brief.questions_skipped > 0:
        content.requirements.append("Defaults applied for skipped questions")
    metadata = ProductDocumentMetadata(
        created_at=brief.created_at,
        interview_duration=brief.interview_duration_seconds,
        questions_asked=brief.questions_asked,
        questions_skipped=brief.questions_skipped,
    )
    return ProductDocument(
        project_type=brief.project_type or brief.scope.type or "project",
        overview=overview,
        timing=timing,
        design=design,
        content=content,
        metadata=metadata,
    )


async def _edit_build_plan(
    state: InterviewState,
    instruction: str,
    model_id: Optional[str] = None,
) -> BuildPlan:
    model_id = model_id or _resolve_interview_model()
    if not model_id:
        raise RuntimeError("No available model for build plan edit")

    payload = {
        "instruction": instruction,
        "current_plan": state.build_plan.model_dump() if state.build_plan else {},
        "brief": state.brief.model_dump(),
    }
    prompt = f"Input JSON:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            response_text = await generate_response(
                messages=[{"role": "user", "content": prompt}],
                model=model_id,
                system_prompt=BUILD_PLAN_EDIT_SYSTEM_PROMPT,
            )
            payload_text = _extract_json(response_text)
            return BuildPlan.model_validate_json(payload_text)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            await asyncio.sleep(2 ** attempt)

    raise RuntimeError(f"Failed to edit build plan: {last_error}")


def _generate_build_plan(brief: ProjectBrief, complexity: str) -> BuildPlan:
    pages: List[str] = brief.scope.pages or []

    project_type = (brief.project_type or brief.scope.type or "").lower()

    if not pages:
        if "saas" in project_type or "dashboard" in project_type:
            pages = ["Home", "Pricing", "Dashboard", "Settings"]
        elif "event" in project_type or "invite" in project_type or "invitation" in project_type:
            pages = ["Invitation", "Details", "RSVP"]
        elif "portfolio" in project_type:
            pages = ["Home", "Work", "About", "Contact"]
        elif "e-commerce" in project_type or "shop" in project_type:
            pages = ["Home", "Products", "Cart", "Checkout"]
        else:
            pages = ["Home", "About", "Contact"]

    page_specs = []
    for idx, page_name in enumerate(pages):
        slug = _slugify(page_name)
        page_specs.append(
            PageSpec(
                id=f"page_{idx}",
                name=page_name,
                path="/" if idx == 0 else f"/{slug}",
                sections=brief.content.sections or [],
                is_main=idx == 0,
            )
        )

    features = []
    if brief.scope.features:
        features.extend(brief.scope.features)
    if brief.technical.integrations:
        features.extend(brief.technical.integrations)
    if brief.technical.auth_required:
        features.append("User authentication")

    design_system: Dict[str, Any] = {}
    if brief.design.colors:
        design_system["colors"] = brief.design.colors
    if brief.design.style:
        design_system["style"] = brief.design.style

    return BuildPlan(
        pages=page_specs,
        design_system=design_system,
        features=features,
        estimated_complexity=complexity,
    )


def _summary_from_brief(brief: ProjectBrief) -> str:
    parts = []
    if brief.scope.type:
        parts.append(brief.scope.type)
    if brief.audience.who:
        parts.append(f"for {brief.audience.who}")
    if brief.goals.primary_goal:
        parts.append(f"goal: {brief.goals.primary_goal}")
    return ", ".join(parts)


def _build_agent_callouts() -> List[AgentCallout]:
    return [
        AgentCallout(agent="RequirementsAgent", content="Synthesizing scope and goals..."),
        AgentCallout(agent="UXAgent", content="Mapping sections and layout..."),
        AgentCallout(agent="TechAgent", content="Checking technical needs..."),
        AgentCallout(agent="PlannerAgent", content="Drafting a build plan..."),
    ]


async def build_first_question_response(
    state: InterviewState,
    user_message: Optional[str] = None,
    preferred_model: Optional[str] = None,
) -> OrchestratorResponse:
    """Create the first ask-group response using the orchestrator LLM."""
    model_id = _resolve_interview_model(preferred_model)
    use_ai = _should_use_ai() and model_id is not None

    if not use_ai:
        return await finalize_interview(
            state,
            reason="ai_unavailable",
            final_status="done",
            model_id=model_id,
        )

    orchestrator = await _call_orchestrator_llm(
        state=state,
        user_message=user_message,
        answers=[],
        action="start",
        model_id=model_id,
    )
    orchestrator = _normalize_orchestrator_response(state, orchestrator)

    orchestrator.brief_patch = _normalize_brief_patch(orchestrator.brief_patch)
    state.brief = apply_brief_patch(state.brief, orchestrator.brief_patch)
    if "complexity" in orchestrator.brief_patch:
        complexity_value = orchestrator.brief_patch.get("complexity")
        if complexity_value in ("low", "medium", "high"):
            state.complexity = complexity_value
            state.brief.complexity = complexity_value

    if isinstance(orchestrator.next_action, AskGroupAction):
        group = orchestrator.next_action.group
        existing_ids = {g.id for g in state.question_plan}
        if group.id in existing_ids:
            for idx, existing in enumerate(state.question_plan):
                if existing.id == group.id:
                    group.is_completed = False
                    state.question_plan[idx] = group
                    break
        else:
            state.question_plan.append(group)
        state.status = "in_progress"
        for idx, existing in enumerate(state.question_plan):
            if existing.id == group.id:
                state.current_group_index = idx
                break
        record_asked_group(state, group)
    elif isinstance(orchestrator.next_action, AskFollowupAction):
        state.status = "in_progress"
        followup_group = QuestionGroup(
            id=f"followup_{uuid4().hex[:6]}",
            topic="follow_up",
            topic_label="Follow-up",
            questions=orchestrator.next_action.questions,
            is_completed=False,
        )
        state.question_plan.append(followup_group)
        state.current_group_index = len(state.question_plan) - 1
        record_asked_group(state, followup_group)
    elif isinstance(orchestrator.next_action, FinishAction):
        state.status = "done"
        state.build_plan = orchestrator.next_action.plan
        state.product_document = orchestrator.next_action.product_document
    elif isinstance(orchestrator.next_action, HandleOfftopicAction):
        state.status = "in_progress"
    elif isinstance(orchestrator.next_action, SuggestEarlyFinishAction):
        state.status = "in_progress"

    return orchestrator


def _ensure_question_options(question: Question) -> Question:
    question.allow_other = True
    if not question.options or len(question.options) == 0:
        question.options = [
            QuestionOption(value="not_sure", label="Not sure"),
            QuestionOption(value="skip", label="Skip"),
        ]
    return question


def _normalize_question_list(questions: List[Question]) -> List[Question]:
    return [_ensure_question_options(question) for question in questions]


def _apply_default_for_question(brief: ProjectBrief, question: Question) -> bool:
    current_value = _get_brief_value(brief, question.slot)
    if current_value not in (None, "", []):
        return False

    default_value = question.default_value
    if default_value is None:
        if question.type == "single_select":
            default_value = question.options[0].value if question.options else None
        elif question.type == "multi_select":
            if question.options:
                default_value = [question.options[0].value]
            else:
                default_value = []
        elif question.type in {"text", "date"}:
            default_value = "TBD"

    if isinstance(default_value, list) and not default_value and question.type == "multi_select":
        _set_brief_value(brief, question.slot, default_value)
        return True

    if default_value is None:
        return False

    if question.type == "multi_select":
        selected = default_value if isinstance(default_value, list) else [default_value]
        answer = InterviewAnswerPayload(
            question_id=question.id,
            raw_text="",
            selected_options=[str(item) for item in selected],
        )
        extracted = _normalize_answer(question, answer)
    elif question.options:
        answer = InterviewAnswerPayload(
            question_id=question.id,
            raw_text="",
            selected_options=[str(default_value)],
        )
        extracted = _normalize_answer(question, answer)
    else:
        answer = InterviewAnswerPayload(
            question_id=question.id,
            raw_text=str(default_value),
            selected_options=None,
        )
        extracted = _normalize_answer(question, answer)

    if not extracted:
        extracted = {question.slot: default_value}

    for slot, value in extracted.items():
        _set_brief_value(brief, slot, value)
    return True


def _apply_defaults_for_questions(state: InterviewState, questions: List[Question]) -> int:
    applied = 0
    for question in questions:
        if _apply_default_for_question(state.brief, question):
            applied += 1
    return applied


def _normalize_brief_patch(patch: Dict[str, Any]) -> Dict[str, Any]:
    if not patch:
        return patch

    normalized = dict(patch)

    design_value = normalized.get("design")
    if isinstance(design_value, str):
        normalized["design"] = {"style": design_value}
    elif isinstance(design_value, dict):
        colors = design_value.get("colors")
        if isinstance(colors, str):
            design_value["colors"] = [colors]

    design_aesthetic = normalized.pop("design_aesthetic", None)
    if design_aesthetic and "design" not in normalized and isinstance(design_aesthetic, dict):
        normalized["design"] = {
            "style": design_aesthetic.get("style"),
            "colors": design_aesthetic.get("colors"),
        }

    content = normalized.get("content")
    if isinstance(content, dict):
        copy_text = content.pop("copy_text", None) or content.pop("copy", None)
        assets = content.get("assets")
        if copy_text:
            if not isinstance(assets, dict):
                assets = {}
            assets["copy"] = copy_text
            content["assets"] = assets
        if isinstance(assets, str):
            lowered = assets.strip().lower()
            if lowered in {"no", "none", "no photos", "no images", "no pictures"}:
                content["assets"] = {"images": []}
            else:
                content["assets"] = {"copy": assets}
        elif isinstance(assets, list):
            content["assets"] = {"images": assets}
        normalized["content"] = content

    scalar_paths = {
        "project_type",
        "language",
        "scope.type",
        "audience.who",
        "audience.context",
        "audience.size",
        "goals.primary_goal",
        "goals.success_criteria",
        "goals.cta",
        "timing.date",
        "timing.time",
        "timing.location",
        "timing.rsvp_deadline",
        "design.style",
        "design.mood",
        "content.assets.copy",
        "content.assets.logo",
    }

    def _coerce_scalar(value: Any) -> Any:
        if isinstance(value, list):
            if not value:
                return None
            first = value[0]
            return first if isinstance(first, str) else str(first)
        return value

    # Normalize dotted keys in patch
    for key, value in list(normalized.items()):
        if key in scalar_paths:
            normalized[key] = _coerce_scalar(value)

    # Normalize nested keys
    for path in scalar_paths:
        if "." not in path:
            continue
        current: Any = normalized
        parts = path.split(".")
        for part in parts[:-1]:
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        if isinstance(current, dict) and parts[-1] in current:
            current[parts[-1]] = _coerce_scalar(current[parts[-1]])

    return normalized


def _normalize_orchestrator_response(
    state: InterviewState,
    orchestrator: OrchestratorResponse,
) -> OrchestratorResponse:
    # Ensure first response shows all agents
    if state.status == "not_started" and not state.asked:
        orchestrator.agent_callouts = _build_agent_callouts()

    next_action = orchestrator.next_action
    if isinstance(next_action, AskGroupAction):
        group_payload = next_action.group.model_dump()
        normalized_questions = _normalize_question_payloads(
            group_payload.get("questions", []),
            state.brief,
        )
        if normalized_questions is None:
            next_action.group.questions = _normalize_question_list(next_action.group.questions)
        else:
            group_payload["questions"] = normalized_questions
            next_action.group = QuestionGroup.model_validate(group_payload)
        next_action.group.is_completed = False
    elif isinstance(next_action, AskFollowupAction):
        questions_payload = [question.model_dump() for question in next_action.questions]
        normalized_questions = _normalize_question_payloads(questions_payload, state.brief)
        if normalized_questions is None:
            next_action.questions = _normalize_question_list(next_action.questions)
        else:
            next_action.questions = [Question.model_validate(q) for q in normalized_questions]
    return orchestrator


def _is_ready_to_finish(state: InterviewState) -> bool:
    if not state.answers:
        return False

    has_project_type = bool(state.brief.project_type or state.brief.scope.type)
    has_audience = bool(state.brief.audience.who)
    has_goal = bool(state.brief.goals.primary_goal)
    has_features_or_sections = bool(state.brief.scope.features or state.brief.content.sections)

    if state.complexity == "low":
        return has_project_type and (has_goal or has_features_or_sections)
    if state.complexity == "medium":
        return has_project_type and has_goal and has_features_or_sections
    return has_project_type and has_audience and has_goal and has_features_or_sections


async def process_first_message(
    project_id: Optional[str],
    message: str,
    template: Optional[Dict[str, str]] = None,
    template_inputs: Optional[Dict[str, str]] = None,
    language: str = "en",
    auto_detect_language: bool = True,
) -> InterviewState:
    """Process user's first message - detect intent and start interview."""
    description = message or " ".join((template_inputs or {}).values())
    complexity = analyze_complexity(description)
    detected_language = _detect_language(message or "") if auto_detect_language else None

    intent = await detect_intent(message)

    brief = ProjectBrief(
        project_type=template.get("name") if template else None,
        complexity=complexity,
        language=detected_language or language,
        created_at=_now_ts(),
    )

    if template_inputs:
        for _, value in template_inputs.items():
            if value and not brief.project_type:
                brief.project_type = value
        brief.scope.type = brief.scope.type or (template.get("name") if template else None)

    _apply_intent_fields(brief, intent.inferred_fields, allow_overwrite=False)

    return InterviewState(
        project_id=project_id,
        status="in_progress",
        complexity=complexity,
        detected_intent=intent.category.value,
        confidence=intent.confidence,
        question_plan=[],
        current_group_index=0,
        asked=[],
        answers=[],
        brief=brief,
        build_plan=None,
    )


def create_initial_state(
    template: Optional[Dict[str, str]] = None,
    template_inputs: Optional[Dict[str, str]] = None,
    user_message: Optional[str] = None,
    language: str = "en",
    auto_detect_language: bool = True,
) -> InterviewState:
    description = user_message or " ".join((template_inputs or {}).values())
    complexity = analyze_complexity(description)
    detected_language = _detect_language(user_message or "") if auto_detect_language else None

    brief = ProjectBrief(
        project_type=template.get("name") if template else None,
        complexity=complexity,
        language=detected_language or language,
        created_at=_now_ts(),
    )

    if template_inputs:
        for key, value in template_inputs.items():
            if value and not brief.project_type:
                brief.project_type = value
        brief.scope.type = brief.scope.type or (template.get("name") if template else None)

    return InterviewState(
        status="not_started",
        complexity=complexity,
        project_id=None,
        question_plan=[],
        current_group_index=0,
        asked=[],
        answers=[],
        brief=brief,
        build_plan=None,
        detected_intent=None,
        confidence=None,
    )


def advance_state_with_answers(
    state: InterviewState,
    answers: List[InterviewAnswerPayload],
    current_group: Optional[QuestionGroup] = None,
) -> bool:
    now = _now_ts()
    brief_patch: Dict[str, Any] = {}

    question_lookup: Dict[str, Question] = {}
    for group in state.question_plan:
        for question in group.questions:
            question_lookup[question.id] = question

    group_question_ids = {q.id for q in current_group.questions} if current_group else set()
    filtered: List[tuple[InterviewAnswerPayload, Question]] = []
    for answer in answers:
        if not _is_nonempty_answer(answer):
            continue
        question = question_lookup.get(answer.question_id)
        if not question:
            continue
        filtered.append((answer, question))

    answered_ids = {question.id for _, question in filtered}
    is_partial = bool(group_question_ids) and bool(answered_ids) and answered_ids != group_question_ids

    for answer, question in filtered:
        extracted = _normalize_answer(question, answer)
        for slot, value in extracted.items():
            _set_brief_value(state.brief, slot, value)
            brief_patch[slot] = value

        state.answers.append(
            CollectedAnswer(
                question_id=answer.question_id,
                raw_text=answer.raw_text,
                selected_options=answer.selected_options,
                extracted=extracted,
                answered_at=now,
                is_partial=is_partial,
            )
        )

    if state.brief:
        state.brief.questions_asked = len(state.answers)
        elapsed = max(now - state.brief.created_at, 0)
        state.brief.interview_duration_seconds = elapsed

    return bool(answered_ids)


def record_answers(state: InterviewState, answers: List[InterviewAnswerPayload]) -> None:
    now = _now_ts()
    for answer in answers:
        state.answers.append(
            CollectedAnswer(
                question_id=answer.question_id,
                raw_text=answer.raw_text or "",
                selected_options=answer.selected_options,
                extracted={},
                answered_at=now,
                is_partial=False,
            )
        )
    if state.brief:
        state.brief.questions_asked = len(state.answers)
        elapsed = max(now - state.brief.created_at, 0)
        state.brief.interview_duration_seconds = elapsed


def record_freeform_answer(state: InterviewState, text: str) -> None:
    now = _now_ts()
    state.answers.append(
        CollectedAnswer(
            question_id=f"freeform_{now}",
            raw_text=text,
            selected_options=None,
            extracted={},
            answered_at=now,
            is_partial=False,
        )
    )
    if state.brief:
        state.brief.questions_asked = len(state.answers)
        elapsed = max(now - state.brief.created_at, 0)
        state.brief.interview_duration_seconds = elapsed


def mark_group_completed(state: InterviewState, group_id: str) -> None:
    for idx, group in enumerate(state.question_plan):
        if group.id == group_id:
            group.is_completed = True
            state.current_group_index = max(state.current_group_index, idx + 1)
            break


def record_asked_group(state: InterviewState, group: QuestionGroup) -> None:
    now = _now_ts()
    for question in group.questions:
        state.asked.append(
            AskedQuestion(
                question_id=question.id,
                group_id=group.id,
                text=question.text,
                asked_at=now,
            )
        )


def get_next_group(state: InterviewState) -> Optional[QuestionGroup]:
    for idx in range(state.current_group_index, len(state.question_plan)):
        group = state.question_plan[idx]
        if not group.is_completed:
            state.current_group_index = idx
            return group
    return None


async def finalize_interview(
    state: InterviewState,
    reason: str = "enough_info",
    final_status: InterviewStatus = "done",
    model_id: Optional[str] = None,
) -> OrchestratorResponse:
    state.status = final_status
    if state.question_plan:
        for group in state.question_plan:
            group.is_completed = True
        state.current_group_index = len(state.question_plan)
    build_plan = _generate_build_plan(state.brief, state.complexity)
    state.build_plan = build_plan
    summary = _summary_from_brief(state.brief)

    try:
        product_document = await _generate_product_document(
            state.brief,
            build_plan,
            model_id=model_id,
        )
    except Exception:
        product_document = _fallback_product_document(state.brief, build_plan)

    state.product_document = product_document

    return OrchestratorResponse(
        mode="finish",
        agent_callouts=_build_agent_callouts(),
        brief_patch={"summary": summary},
        next_action=FinishAction(
            type="finish",
            brief=state.brief,
            plan=build_plan,
            product_document=product_document,
        ),
        confidence=0.7,
        reason_codes=[f"finish_reason:{reason}"],
        user_sentiment="neutral",
    )


async def orchestrate_turn(
    state: InterviewState,
    action: str,
    answers: Optional[List[InterviewAnswerPayload]] = None,
    user_message: Optional[str] = None,
    preferred_model: Optional[str] = None,
) -> OrchestratorResponse:
    answers = answers or []
    model_id = _resolve_interview_model(preferred_model)

    # User wants to finish immediately
    if action in {"generate_now", "skip_all"}:
        remaining = 0
        if state.question_plan:
            for group in state.question_plan:
                if not group.is_completed:
                    remaining += len(group.questions)
                    _apply_defaults_for_questions(state, group.questions)
                    group.is_completed = True
            state.current_group_index = len(state.question_plan)
        if state.brief:
            state.brief.questions_skipped += remaining
            state.brief.questions_skipped = max(state.brief.questions_skipped, 0)
        final_status: InterviewStatus = "skipped" if action == "skip_all" else "done"
        return await finalize_interview(
            state,
            reason="user_generate_now",
            final_status=final_status,
            model_id=model_id,
        )

    # If interview already finished, treat messages as build plan edits
    if (
        state.build_plan
        and state.status in {"finishing", "done", "skipped"}
        and action == "answer"
        and user_message
    ):
        updated_plan = state.build_plan
        if _should_use_ai() and model_id is not None:
            try:
                updated_plan = await _edit_build_plan(
                    state,
                    user_message,
                    model_id=model_id,
                )
            except Exception:
                updated_plan = state.build_plan
        state.build_plan = updated_plan
        try:
            state.product_document = await _generate_product_document(
                state.brief,
                state.build_plan,
                model_id=model_id,
            )
        except Exception:
            state.product_document = _fallback_product_document(state.brief, state.build_plan)
        return OrchestratorResponse(
            mode="finish",
            agent_callouts=_build_agent_callouts(),
            brief_patch={},
            next_action=FinishAction(
                type="finish",
                brief=state.brief,
                plan=state.build_plan,
                product_document=state.product_document,
            ),
            confidence=0.6,
            reason_codes=["plan_edit"],
            user_sentiment="neutral",
        )

    current_group = get_next_group(state)

    if action == "skip" and current_group:
        state.brief.questions_skipped += len(current_group.questions)
        _apply_defaults_for_questions(state, current_group.questions)
        mark_group_completed(state, current_group.id)
        if state.brief:
            state.brief.questions_skipped = max(state.brief.questions_skipped, 0)

    filtered_answers = [answer for answer in answers if _is_nonempty_answer(answer)]
    answered_any = False
    if filtered_answers:
        answered_any = advance_state_with_answers(state, filtered_answers, current_group)
    elif user_message:
        record_freeform_answer(state, user_message)

    use_ai = _should_use_ai() and model_id is not None

    if use_ai:
        orchestrator = await _call_orchestrator_llm(
            state,
            user_message,
            filtered_answers,
            action,
            model_id=model_id,
        )
        orchestrator = _normalize_orchestrator_response(state, orchestrator)
    else:
        return await finalize_interview(
            state,
            reason="ai_unavailable",
            final_status="done",
            model_id=model_id,
        )

    # Apply brief updates from LLM
    orchestrator.brief_patch = _normalize_brief_patch(orchestrator.brief_patch)
    state.brief = apply_brief_patch(state.brief, orchestrator.brief_patch)
    if "complexity" in orchestrator.brief_patch:
        complexity_value = orchestrator.brief_patch.get("complexity")
        if complexity_value in ("low", "medium", "high"):
            state.complexity = complexity_value
            state.brief.complexity = complexity_value

    # Update state based on next_action
    if isinstance(orchestrator.next_action, AskGroupAction):
        group = orchestrator.next_action.group
        existing_ids = {g.id for g in state.question_plan}
        if group.id in existing_ids:
            for idx, existing in enumerate(state.question_plan):
                if existing.id == group.id:
                    group.is_completed = False
                    state.question_plan[idx] = group
                    break
        else:
            state.question_plan.append(group)
        state.status = "in_progress"
        for idx, existing in enumerate(state.question_plan):
            if existing.id == group.id:
                state.current_group_index = idx
                break
        if current_group and current_group.id != group.id:
            mark_group_completed(state, current_group.id)
        record_asked_group(state, group)
    elif isinstance(orchestrator.next_action, AskFollowupAction):
        state.status = "in_progress"
        followup_group = QuestionGroup(
            id=f"followup_{uuid4().hex[:6]}",
            topic="follow_up",
            topic_label="Follow-up",
            questions=orchestrator.next_action.questions,
            is_completed=False,
        )
        state.question_plan.append(followup_group)
        state.current_group_index = len(state.question_plan) - 1
        record_asked_group(state, followup_group)
    elif isinstance(orchestrator.next_action, FinishAction):
        state.status = "done"
        state.build_plan = orchestrator.next_action.plan
        state.product_document = orchestrator.next_action.product_document
    elif isinstance(orchestrator.next_action, HandleOfftopicAction):
        state.status = "in_progress"
    elif isinstance(orchestrator.next_action, SuggestEarlyFinishAction):
        state.status = "in_progress"

    return orchestrator
