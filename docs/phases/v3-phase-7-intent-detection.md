# Phase 7: Intent Detection

**Duration**: Week 6
**Status**: Pending
**Depends On**: Phase 1 (Build Runtime Foundation)

---

## Phase Overview

This phase implements intent detection - the ability to detect what type of project the user wants to create from their first message, then start the appropriate interview flow. This replaces the template selection page.

---

## Prerequisites

### Must Be Completed Before Starting
1. **Phase 1 complete** - Models and storage
2. **Interview orchestrator exists** - `app/services/interview_orchestrator.py`

### External Dependencies
- **AI service** - For intent classification

---

## Detailed Tasks

### Task 7.1: Create Intent Detection Service

**Description**: Implement intent detection based on user message

**File: `backend/app/services/intent_detection.py`**

```python
from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum

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

# Intent patterns and keywords
INTENT_PATTERNS = {
    IntentCategory.EVENT_INVITATION: {
        "keywords": ["wedding", "birthday", "party", "rsvp", "invitation", "event"],
        "questions": [
            "What's the date and time of the event?",
            "Where will it be held?",
            "What's the RSVP deadline?"
        ]
    },
    IntentCategory.LANDING_PAGE: {
        "keywords": ["landing", "saas", "product", "launch", "marketing"],
        "questions": [
            "What's the main value proposition?",
            "Who's your target audience?",
            "What's the primary CTA?"
        ]
    },
    IntentCategory.PORTFOLIO: {
        "keywords": ["portfolio", "about", "profile", "personal", "bio"],
        "questions": [
            "What's your name/profession?",
            "What projects should I showcase?",
            "Any social links to include?"
        ]
    },
    # ... more patterns
}

async def detect_intent(message: str) -> DetectedIntent:
    """Detect user intent from first message."""
    message_lower = message.lower()

    # Check each intent category
    best_match = None
    best_score = 0

    for category, pattern in INTENT_PATTERNS.items():
        matches = sum(1 for kw in pattern["keywords"] if kw in message_lower)
        if matches > 0:
            score = matches * 0.25  # Each keyword adds 0.25
            if score > best_score:
                best_score = score
                best_match = category

    if best_match:
        return DetectedIntent(
            category=best_match,
            confidence=min(0.5 + best_score, 0.95),
            inferred_fields=_extract_fields(best_match, message),
            suggested_questions=INTENT_PATTERNS[best_match]["questions"]
        )

    # Fallback to other
    return DetectedIntent(
        category=IntentCategory.OTHER,
        confidence=0.3,
        inferred_fields={},
        suggested_questions=[
            "Can you tell me more about what you want to build?",
            "Who is this page for?",
            "What's the main goal?"
        ]
    )

def _extract_fields(category: IntentCategory, message: str) -> Dict[str, str]:
    """Extract known fields from message based on category."""
    # Simple extraction - can be enhanced with regex/NER
    fields = {}

    if category == IntentCategory.EVENT_INVITATION:
        # Look for date patterns
        import re
        dates = re.findall(r'\w+\s+\d+', message)
        if dates:
            fields["date"] = dates[0]

    return fields
```

**Dependencies**: None (self-contained)
**Parallelizable**: Yes (with Task 7.2)

---

### Task 7.2: Update Interview Orchestrator

**Description**: Modify interview orchestrator to use detected intent

**File: `backend/app/services/interview_orchestrator.py` (modifications)**

```python
async def process_first_message(
    self,
    project_id: str,
    message: str
) -> InterviewState:
    """Process user's first message - detect intent and start interview."""
    # Detect intent
    intent = await detect_intent(message)

    # Create interview state with detected intent
    state = InterviewState(
        project_id=project_id,
        status="in_progress",
        detected_intent=intent.category.value,
        confidence=intent.confidence,
        # Generate questions based on intent
        question_plan=self._generate_questions(intent),
        current_group_index=0
    )

    # Extract any fields already provided
    state.brief.update(intent.inferred_fields)

    await self.storage.save(state)

    return state

def _generate_questions(self, intent: DetectedIntent) -> List[QuestionGroup]:
    """Generate question groups based on detected intent."""
    # Implementation here
```

**Dependencies**: Task 7.1
**Parallelizable**: No

---

### Task 7.3: Update Chat API

**Description**: Modify chat API to trigger intent detection on first message

**File: `backend/app/api/chat.py` (modifications)**

```python
@router.post("/api/projects/{project_id}/chat")
async def chat_message(
    project_id: str,
    message: ChatMessage,
    user=Depends(get_current_user)
):
    """Chat endpoint with intent detection."""

    # Get interview state
    state = await storage.get_interview(project_id)

    # First message? Detect intent and start interview
    if state.status == "not_started":
        intent_result = await detect_intent(message.content)

        state = await interview_orchestrator.process_first_message(
            project_id=project_id,
            message=message.content
        )

        # Stream questions
        return StreamingResponse(
            stream_interview_questions(state)
        )

    # ... rest of chat handling
```

**Dependencies**: Tasks 7.1, 7.2
**Parallelizable**: No

---

### Task 7.4: Test Intent Detection

**Description**: Create comprehensive tests for intent detection

**File: `backend/tests/unit/services/test_intent_detection.py`**

```python
import pytest
from app.services.intent_detection import detect_intent, DetectedIntent

@pytest.mark.asyncio
async def test_detect_event_invitation():
    """Test detection of event invitation intent."""
    result = await detect_intent("I need a wedding RSVP page for Emma and John's wedding")
    assert result.category == IntentCategory.EVENT_INVITATION
    assert result.confidence > 0.5

@pytest.mark.asyncio
async def test_detect_landing_page():
    """Test detection of landing page intent."""
    result = await detect_intent("I want to create a SaaS landing page for my startup")
    assert result.category == IntentCategory.LANDING_PAGE
    assert result.confidence > 0.5

# ... more tests
```

**Dependencies**: Tasks 7.1, 7.2, 7.3
**Parallelizable**: No

---

## Acceptance Criteria

- [ ] Intent detection identifies 8+ project types
- [ ] Confidence score reflects match quality
- [ ] Inferred fields are extracted from messages
- [ ] Questions are tailored to detected intent
- [ ] Interview orchestrator uses detected intent
- [ ] Chat API triggers intent detection on first message
- [ ] Tests achieve >90% accuracy on test cases
- [ ] Fallback works for unrecognized messages

---

## Estimated Scope

**Complexity**: Medium

**Key Effort Drivers**:
- Defining intent patterns and keywords
- Testing accuracy across message variations
- Integrating with existing interview flow

**Estimated Lines of Code**: ~300-500

---

## Testing Strategy

### Unit Tests
- Test each intent category detection
- Test confidence scoring
- Test field extraction

### Integration Tests
- Test full chat flow with intent detection
- Test question generation based on intent

### Test Files
- `backend/tests/unit/services/test_intent_detection.py`
- `backend/tests/integration/test_chat_intent.py`
