"""Build runtime agents for planning, implementation, and review."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, Field

from .models import BuildGraph, PatchSet, ReviewReport, TokenUsage

T = TypeVar("T", bound=BaseModel)


class AgentResult(BaseModel):
    output: Dict[str, Any]
    raw_response: str
    tokens_used: int = 0
    model: str = "glm-4.7"
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


class BaseAgent(ABC):
    def __init__(self, model: str = "glm-4.7") -> None:
        self.model = model
        self.temperature = 0.3
        self.system_prompt = self._get_system_prompt()

    @abstractmethod
    def _get_system_prompt(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _get_output_type(self) -> Type[T]:
        raise NotImplementedError

    def _build_user_message(self, inputs: Dict[str, Any]) -> str:
        return json.dumps(inputs, indent=2)

    async def run(self, **inputs: Any) -> AgentResult:
        user_msg = self._build_user_message(inputs)
        llm_response = await self._call_llm(user_msg)
        if isinstance(llm_response, str):
            content = llm_response
            usage = TokenUsage()
            model_name = self.model
        else:
            content = llm_response.content
            usage = TokenUsage(
                prompt_tokens=llm_response.usage.prompt_tokens,
                completion_tokens=llm_response.usage.completion_tokens,
                total_tokens=llm_response.usage.total_tokens,
            )
            model_name = llm_response.model
        parsed = self._parse_output(content)
        output_model = self._get_output_type().model_validate(parsed)
        output = output_model.model_dump(mode="json")
        return AgentResult(
            output=output,
            raw_response=content,
            tokens_used=usage.total_tokens,
            model=model_name,
            token_usage=usage,
        )

    async def _call_llm(self, user_message: str):
        from app.services.ai_service import chat_complete

        return await chat_complete(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=self.temperature,
        )

    def _strip_code_fence(self, text: str) -> str:
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    def _extract_json_text(self, text: str) -> Optional[str]:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
        return None

    def _sanitize_json(self, text: str) -> str:
        """Escape invalid control characters inside JSON strings."""
        out: list[str] = []
        in_string = False
        escape = False
        for ch in text:
            if escape:
                out.append(ch)
                escape = False
                continue
            if ch == "\\":
                out.append(ch)
                escape = True
                continue
            if ch == '"':
                out.append(ch)
                in_string = not in_string
                continue
            if in_string and ord(ch) < 0x20:
                if ch == "\n":
                    out.append("\\n")
                elif ch == "\r":
                    out.append("\\r")
                elif ch == "\t":
                    out.append("\\t")
                else:
                    out.append(f"\\u{ord(ch):04x}")
                continue
            out.append(ch)
        return "".join(out)

    def _parse_output(self, response: str) -> Dict[str, Any]:
        text = self._strip_code_fence(response)
        if not text:
            raise ValueError("Empty response from model")
        candidates = [text]
        extracted = self._extract_json_text(text)
        if extracted:
            candidates.append(extracted)
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                sanitized = self._sanitize_json(candidate)
                try:
                    return json.loads(sanitized)
                except json.JSONDecodeError:
                    continue
        raise ValueError(f"Invalid JSON: {text[:200]}")


class PlannerAgent(BaseAgent):
    def _get_system_prompt(self) -> str:
        return (
            "You are PlannerAgent for Zaoya. Create BuildGraph from brief.\n\n"
            "Output JSON:\n"
            "{\n"
            '  "tasks": [{"id": "task_001", "title": "...", "goal": "...", '
            '"acceptance": [...], "depends_on": [], "files_expected": [...], '
            '"status": "todo"}],\n'
            '  "notes": "..." \n'
            "}\n\n"
            "Rules: <=15 tasks, each <=5 files, clear acceptance criteria, "
            "Zaoya platform (mobile-first, Tailwind, Zaoya.* functions, "
            "NO fetch/XHR/storage/eval)\n\n"
            "Output ONLY valid JSON."
        )

    def _get_output_type(self) -> Type[BuildGraph]:
        return BuildGraph

    def _build_user_message(self, inputs: Dict[str, Any]) -> str:
        return (
            "# Brief\n"
            f"{json.dumps(inputs.get('brief', {}), indent=2)}\n\n"
            "# Build Plan\n"
            f"{json.dumps(inputs.get('build_plan', {}), indent=2)}\n\n"
            "# Product Doc\n"
            f"{json.dumps(inputs.get('product_doc', {}), indent=2)}\n\n"
            "Create BuildGraph:"
        )


class ImplementerAgent(BaseAgent):
    def __init__(self, model: str = "glm-4.7") -> None:
        super().__init__(model)
        self.temperature = 0.2

    def _get_system_prompt(self) -> str:
        return (
            "You are ImplementerAgent for Zaoya. Generate unified diff.\n\n"
            "Output JSON:\n"
            "{\n"
            '  "id": "ps_001", "task_id": "task_001", "diff": "...", '
            '"touched_files": [...], "notes": "..." \n'
            "}\n\n"
            "Rules: Output ONLY valid JSON, proper diff format, <=5 files, "
            "Zaoya.* functions, NO fetch/XHR/storage/eval."
        )

    def _get_output_type(self) -> Type[PatchSet]:
        return PatchSet

    def _build_user_message(self, inputs: Dict[str, Any]) -> str:
        task = inputs.get("task", {})
        files = inputs.get("relevant_files", {})
        state = inputs.get("state")
        context = inputs.get("context")
        acceptance = task.get("acceptance", []) or []
        msg = f"# Task\n{json.dumps(task, indent=2)}\n\n# Acceptance\n"
        if acceptance:
            msg += "\n".join(f"- {item}" for item in acceptance)
        else:
            msg += "- None"
        if state:
            msg += f"\n\n# Build State\n{json.dumps(state, indent=2)}"
        if context:
            msg += f"\n\n# Context\n{json.dumps(context, indent=2)}"
        for path, content in files.items():
            snippet = content[:500]
            msg += f"\n\n## {path}\n```\n{snippet}\n```\n"
        return msg


class ReviewerAgent(BaseAgent):
    def _get_system_prompt(self) -> str:
        return (
            "You are ReviewerAgent for Zaoya. Review patch.\n\n"
            "Output JSON:\n"
            "{\n"
            '  "decision": "approve" | "request_changes",\n'
            '  "reasons": [...],\n'
            '  "required_fixes": [...]\n'
            "}\n\n"
            "APPROVE if: all criteria met, validation passed, checks passed, "
            "no security issues.\n"
            "REQUEST_CHANGES otherwise. NO fetch/XHR/storage/eval.\n\n"
            "Output ONLY valid JSON."
        )

    def _get_output_type(self) -> Type[ReviewReport]:
        return ReviewReport

    def _build_user_message(self, inputs: Dict[str, Any]) -> str:
        return (
            "# Task\n"
            f"{json.dumps(inputs.get('task', {}), indent=2)}\n\n"
            "# Patch\n"
            f"{json.dumps(inputs.get('patchset', {}), indent=2)}\n\n"
            "# Validation\n"
            f"{json.dumps(inputs.get('validation_report', {}), indent=2)}\n\n"
            "# Checks\n"
            f"{json.dumps(inputs.get('check_report', {}), indent=2)}\n\n"
            "Review:"
        )


def create_planner_agent(model: str = "glm-4.7") -> PlannerAgent:
    return PlannerAgent(model)


def create_implementer_agent(model: str = "glm-4.7") -> ImplementerAgent:
    return ImplementerAgent(model)


def create_reviewer_agent(model: str = "glm-4.7") -> ReviewerAgent:
    return ReviewerAgent(model)


planner = create_planner_agent()
implementer = create_implementer_agent()
reviewer = create_reviewer_agent()

__all__ = [
    "AgentResult",
    "BaseAgent",
    "PlannerAgent",
    "ImplementerAgent",
    "ReviewerAgent",
    "create_planner_agent",
    "create_implementer_agent",
    "create_reviewer_agent",
    "planner",
    "implementer",
    "reviewer",
]
