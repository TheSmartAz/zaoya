"""Interview API endpoints for generating adaptive questions."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.models.schemas.interview import InterviewTurnRequest, InterviewTurnResponse
from app.services.interview_orchestrator import create_initial_state, orchestrate_turn
from ..services.ai_service import generate_response

router = APIRouter(prefix="/api", tags=["interview"])

INTERVIEW_SYSTEM_PROMPT = (
    "You are a product designer helping a user craft requirements for a web page. "
    "Ask only focused, high-impact questions and follow the requested response format."
)


class InterviewRequest(BaseModel):
    template: Dict[str, str]
    knownFacts: Dict[str, str]
    questionsAsked: List[str]


class InterviewQuestion(BaseModel):
    id: str
    question: str
    type: str
    options: Optional[List[str]] = None
    skipLabel: Optional[str] = None


class InterviewResponse(BaseModel):
    readyToGenerate: bool
    questions: List[InterviewQuestion] = []


@router.post("/interview", response_model=InterviewResponse)
async def get_interview_questions(request: InterviewRequest):
    """Generate interview questions based on template and known facts.

    Uses AI to determine what critical information is missing and asks
    focused questions to improve first-generation quality.
    """
    from ..services.prompt_builder import build_interview_prompt

    prompt = build_interview_prompt(
        request.template,
        request.knownFacts,
        request.questionsAsked,
    )

    try:
        response_text = await generate_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=INTERVIEW_SYSTEM_PROMPT,
        )

        # Parse AI response
        if "READY_TO_GENERATE: true" in response_text:
            return InterviewResponse(readyToGenerate=True, questions=[])

        questions = _parse_questions(response_text)
        return InterviewResponse(readyToGenerate=False, questions=questions)

    except Exception:
        # On error, allow proceeding without questions
        return InterviewResponse(readyToGenerate=True, questions=[])


def _parse_questions(text: str) -> List[InterviewQuestion]:
    """Parse AI response into structured questions.

    Expected format:
    QUESTIONS:
    1. Question text | OPTIONS: [opt1, opt2, opt3] | SKIP: skip text
    2. Question text | TYPE: text | SKIP: skip text
    """
    questions = []

    # Extract questions section
    if "QUESTIONS:" not in text:
        return questions

    questions_section = text.split("QUESTIONS:")[1].strip()
    lines = questions_section.split("\n")

    for i, line in enumerate(lines):
        if not line.strip() or not line[0].isdigit():
            continue

        # Remove numbering (1., 2., etc.)
        line = line.split(".", 1)[1].strip() if "." in line else line

        parts = [p.strip() for p in line.split("|")]
        if not parts:
            continue

        question_text = parts[0]
        question_type = "single"  # default
        options: Optional[List[str]] = None
        skip_label = "Not sure—choose for me"

        for part in parts[1:]:
            if part.startswith("OPTIONS:"):
                options_str = part.split("OPTIONS:")[1].strip()
                # Parse options format: [opt1, opt2, opt3]
                options_str = options_str.strip("[]")
                options = [o.strip().strip('"').strip("'") for o in options_str.split(",")]
                question_type = "single" if len(options) > 1 else "multi"
            elif part.startswith("TYPE:"):
                question_type = part.split("TYPE:")[1].strip()
            elif part.startswith("SKIP:"):
                skip_label = part.split("SKIP:")[1].strip()

        questions.append(
            InterviewQuestion(
                id=f"q_{i}_{hash(question_text) % 10000}",
                question=question_text,
                type=question_type,
                options=options,
                skipLabel=skip_label,
            )
        )

    return questions


@router.post("/interview/v2", response_model=InterviewTurnResponse)
async def interview_turn(request: InterviewTurnRequest) -> InterviewTurnResponse:
    state = request.state
    if request.action == "start" or state is None:
        state = create_initial_state(
            template=request.template,
            template_inputs=request.templateInputs,
            user_message=request.userMessage,
        )

    orchestrator = await orchestrate_turn(
        state=state,
        action=request.action,
        answers=request.answers,
        user_message=request.userMessage,
    )
    return InterviewTurnResponse(state=state, orchestrator=orchestrator)
