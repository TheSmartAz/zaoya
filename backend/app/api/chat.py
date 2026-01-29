"""Chat API with SSE streaming"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models import ChatRequest
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest):
    """AI chat endpoint with SSE streaming"""
    from app.services.ai_service import stream_chat
    from app.services.prompt_builder import build_system_prompt, format_quick_action_prompt

    model = request.model or "glm-4.7"
    messages = [msg.model_dump() for msg in request.messages]
    system_prompt = None

    template = request.template.model_dump() if request.template else None
    template_inputs = request.templateInputs or {}
    interview_answers = request.interviewAnswers or {}

    if template:
        combined_inputs = {**template_inputs, **interview_answers}
        system_prompt = build_system_prompt(template, combined_inputs)

    if request.isQuickAction and messages:
        for message in reversed(messages):
            if message.get("role") == "user":
                message["content"] = format_quick_action_prompt(
                    message.get("content", ""),
                    template or {},
                )
                break

    async def generate():
        stream = await stream_chat(messages, model, system_prompt=system_prompt)
        async for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'choices': [{'delta': {'content': delta.content}}]})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/models")
async def get_models():
    """Get available AI models"""
    from app.services.ai_service import get_available_models
    return {"models": get_available_models()}
