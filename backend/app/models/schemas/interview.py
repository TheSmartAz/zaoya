"""Pydantic schemas for the v2 adaptive interview flow."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal, Union, Annotated
from pydantic import BaseModel, Field, ConfigDict


InterviewStatus = Literal["not_started", "in_progress", "finishing", "done", "skipped"]
InterviewComplexity = Literal["low", "medium", "high"]


class QuestionOption(BaseModel):
    value: str
    label: str
    description: Optional[str] = None


class Question(BaseModel):
    id: str
    text: str
    type: Literal["single_select", "multi_select", "text", "date"]
    options: Optional[List[QuestionOption]] = None
    allow_other: bool = True
    slot: str
    default_value: Optional[Any] = None


class QuestionGroup(BaseModel):
    id: str
    topic: str
    topic_label: str
    questions: List[Question]
    is_completed: bool = False


class AskedQuestion(BaseModel):
    question_id: str
    group_id: str
    text: str
    asked_at: int


class CollectedAnswer(BaseModel):
    question_id: str
    raw_text: str
    selected_options: Optional[List[str]] = None
    extracted: Dict[str, Any] = Field(default_factory=dict)
    answered_at: int
    is_partial: bool = False


class BriefScope(BaseModel):
    type: Optional[str] = None
    pages: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)


class BriefAudience(BaseModel):
    who: Optional[str] = None
    context: Optional[str] = None
    size: Optional[str] = None


class BriefGoals(BaseModel):
    primary_goal: Optional[str] = None
    success_criteria: Optional[str] = None
    cta: Optional[str] = None


class BriefTiming(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    rsvp_deadline: Optional[str] = None


class BriefContentAssets(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    logo: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    copy_text: Optional[str] = Field(default=None, alias="copy")


class BriefContent(BaseModel):
    sections: List[str] = Field(default_factory=list)
    assets: BriefContentAssets = Field(default_factory=BriefContentAssets)


class BriefDesign(BaseModel):
    style: Optional[str] = None
    colors: List[str] = Field(default_factory=list)
    mood: Optional[str] = None


class BriefTechnical(BaseModel):
    auth_required: Optional[bool] = None
    integrations: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)


class ProjectBrief(BaseModel):
    project_type: Optional[str] = None
    complexity: InterviewComplexity = "medium"
    scope: BriefScope = Field(default_factory=BriefScope)
    audience: BriefAudience = Field(default_factory=BriefAudience)
    goals: BriefGoals = Field(default_factory=BriefGoals)
    timing: BriefTiming = Field(default_factory=BriefTiming)
    content: BriefContent = Field(default_factory=BriefContent)
    design: BriefDesign = Field(default_factory=BriefDesign)
    technical: BriefTechnical = Field(default_factory=BriefTechnical)
    language: str = "en"
    created_at: int = 0
    interview_duration_seconds: int = 0
    questions_asked: int = 0
    questions_skipped: int = 0


class PageSpec(BaseModel):
    id: str
    name: str
    path: str
    sections: List[str]
    is_main: bool = False


class BuildPlan(BaseModel):
    pages: List[PageSpec] = Field(default_factory=list)
    design_system: Dict[str, Any] = Field(default_factory=dict)
    features: List[str] = Field(default_factory=list)
    estimated_complexity: str = "medium"


class ProductDocumentOverview(BaseModel):
    name: str
    description: str
    target_audience: str


class ProductDocumentTiming(BaseModel):
    date: str
    time: str
    duration: Optional[str] = None
    location: Optional[str] = None


class ProductDocumentDesign(BaseModel):
    theme: str
    color_palette: List[str] = Field(default_factory=list)
    style_keywords: List[str] = Field(default_factory=list)


class ProductDocumentContent(BaseModel):
    sections: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)


class ProductDocumentContact(BaseModel):
    methods: List[str] = Field(default_factory=list)
    info: str = ""


class ProductDocumentMetadata(BaseModel):
    created_at: int = 0
    interview_duration: int = 0
    questions_asked: int = 0
    questions_skipped: int = 0


class ProductDocument(BaseModel):
    project_type: str
    overview: ProductDocumentOverview
    timing: Optional[ProductDocumentTiming] = None
    design: ProductDocumentDesign
    content: ProductDocumentContent
    contact: Optional[ProductDocumentContact] = None
    metadata: ProductDocumentMetadata


class InterviewState(BaseModel):
    status: InterviewStatus = "not_started"
    complexity: InterviewComplexity = "medium"
    project_id: Optional[str] = None
    question_plan: List[QuestionGroup] = Field(default_factory=list)
    current_group_index: int = 0
    asked: List[AskedQuestion] = Field(default_factory=list)
    answers: List[CollectedAnswer] = Field(default_factory=list)
    brief: ProjectBrief = Field(default_factory=ProjectBrief)
    build_plan: Optional[BuildPlan] = None
    product_document: Optional[ProductDocument] = None
    detected_intent: Optional[str] = None
    confidence: Optional[float] = None


class AgentCallout(BaseModel):
    agent: Literal["RequirementsAgent", "UXAgent", "TechAgent", "PlannerAgent"]
    content: str


class AskGroupAction(BaseModel):
    type: Literal["ask_group"]
    group: QuestionGroup


class AskFollowupAction(BaseModel):
    type: Literal["ask_followup"]
    questions: List[Question]
    reason: str


class FinishAction(BaseModel):
    type: Literal["finish"]
    brief: ProjectBrief
    plan: BuildPlan
    product_document: ProductDocument


class HandleOfftopicAction(BaseModel):
    type: Literal["handle_offtopic"]
    response: str
    return_to: str


class SuggestEarlyFinishAction(BaseModel):
    type: Literal["suggest_early_finish"]
    message: str


NextAction = Annotated[
    Union[
        AskGroupAction,
        AskFollowupAction,
        FinishAction,
        HandleOfftopicAction,
        SuggestEarlyFinishAction,
    ],
    Field(discriminator="type"),
]


class OrchestratorResponse(BaseModel):
    mode: Literal["interview", "off_topic", "finish"]
    agent_callouts: List[AgentCallout] = Field(default_factory=list)
    brief_patch: Dict[str, Any] = Field(default_factory=dict)
    next_action: NextAction
    confidence: float = 0.5
    reason_codes: List[str] = Field(default_factory=list)
    user_sentiment: Literal["engaged", "neutral", "impatient", "frustrated"] = "neutral"


class AssistantMessage(BaseModel):
    type: Literal[
        "text",
        "agent_callout",
        "question_group",
        "followup_questions",
        "build_plan",
        "product_document",
        "generating",
    ]
    content: Optional[str] = None
    agent: Optional[str] = None
    group: Optional[QuestionGroup] = None
    questions: Optional[List[Question]] = None
    plan: Optional[BuildPlan] = None
    product_document: Optional[ProductDocument] = None
    progress: Optional[int] = None
    current_page: Optional[str] = None


class InterviewControls(BaseModel):
    can_skip: bool = True
    can_generate_now: bool = True
    can_go_back: bool = False
    can_edit_via_chat: bool = False
    can_generate: bool = False


class InterviewAnswerPayload(BaseModel):
    question_id: str
    raw_text: str
    selected_options: Optional[List[str]] = None


class InterviewTurnRequest(BaseModel):
    projectId: Optional[str] = None
    template: Optional[Dict[str, str]] = None
    templateInputs: Dict[str, str] = Field(default_factory=dict)
    userMessage: Optional[str] = None
    language: Optional[str] = None
    auto_detect_language: bool = True
    model: Optional[str] = None
    action: Literal["start", "answer", "skip", "generate_now", "skip_all"] = "answer"
    answers: List[InterviewAnswerPayload] = Field(default_factory=list)
    state: Optional[InterviewState] = None


class InterviewTurnResponse(BaseModel):
    state: InterviewState
    orchestrator: OrchestratorResponse


class InterviewChatRequest(BaseModel):
    role: Literal["user"] = "user"
    content: str = ""
    selected_options: Optional[List[str]] = None
    action: Optional[Literal["skip", "generate_now", "skip_all"]] = None
    template: Optional[Dict[str, str]] = None
    templateInputs: Dict[str, str] = Field(default_factory=dict)
    language: Optional[str] = None
    auto_detect_language: bool = True
    model: Optional[str] = None
    answers: List[InterviewAnswerPayload] = Field(default_factory=list)
    state: Optional[InterviewState] = None


class InterviewStateSnapshot(BaseModel):
    status: InterviewStatus
    complexity: InterviewComplexity
    current_question_number: int
    brief_coverage: float


class InterviewChatResponse(BaseModel):
    assistant_messages: List[AssistantMessage] = Field(default_factory=list)
    interview_state: InterviewStateSnapshot
    controls: InterviewControls
    state: Optional[InterviewState] = None
