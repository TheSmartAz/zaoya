# Phase 3: Agents

**Duration**: Week 3
**Status**: Pending
**Depends On**: Phase 1 (Build Runtime Foundation)

---

## Phase Overview

This phase implements the three core agents:
1. **PlannerAgent** - Creates BuildGraph from brief/plan/doc
2. **ImplementerAgent** - Generates PatchSet for tasks
3. **ReviewerAgent** - Evaluates patches and decides

---

## Prerequisites

- Phase 1 complete (models exist)
- AI service integration (`app/services/ai_service.py`)

---

## Detailed Tasks

### Task 3.1: Create Base Agent Framework

```python
# agents.py
import json
from abc import ABC, abstractmethod
from typing import Dict, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class AgentResult(BaseModel):
    output: Dict
    raw_response: str
    tokens_used: int = 0
    model: str = "glm-4.7"

class BaseAgent(ABC):
    def __init__(self, model: str = "glm-4.7"):
        self.model = model
        self.system_prompt = self._get_system_prompt()

    @abstractmethod
    def _get_system_prompt(self) -> str: pass
    @abstractmethod
    def _get_output_type(self) -> Type[BaseModel]: pass

    async def run(self, **inputs) -> AgentResult:
        user_msg = json.dumps(inputs, indent=2)
        response = await self._call_llm(user_msg)
        parsed = self._parse_output(response)
        return AgentResult(output=parsed, raw_response=response)

    async def _call_llm(self, user_message: str) -> str:
        from app.services.ai_service import ai_service
        return await ai_service.chat_complete(
            model=self.model,
            messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": user_message}],
            temperature=0.3
        )

    def _parse_output(self, response: str) -> Dict:
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].strip() == "```": lines = lines[:-1]
            text = "\n".join(lines)
        try: return json.loads(text)
        except json.JSONDecodeError: raise ValueError(f"Invalid JSON: {text[:100]}")
```

### Task 3.2: Implement PlannerAgent

```python
class PlannerAgent(BaseAgent):
    def _get_system_prompt(self) -> str:
        return """You are PlannerAgent for Zaoya. Create BuildGraph from brief.

Output JSON:
{
  "tasks": [{"id": "task_001", "title": "...", "goal": "...", "acceptance": [...], "depends_on": [], "files_expected": [...], "status": "todo"}],
  "notes": "..."
}

Rules: <=15 tasks, each <=5 files, clear acceptance criteria, Zaoya platform (mobile-first, Tailwind, Zaoya.* functions, NO fetch/XHR/storage/eval)

Output ONLY valid JSON."""

    def _get_output_type(self): from .models import BuildGraph; return BuildGraph

    def _build_user_message(self, inputs: Dict) -> str:
        return f"# Brief\n{json.dumps(inputs.get('brief', {}))}\n\n# Build Plan\n{json.dumps(inputs.get('build_plan', {}))}\n\n# Product Doc\n{json.dumps(inputs.get('product_doc', {}))}\n\nCreate BuildGraph:"
```

### Task 3.3: Implement ImplementerAgent

```python
class ImplementerAgent(BaseAgent):
    def __init__(self, model: str = "glm-4.7"):
        super().__init__(model)
        self.temperature = 0.2

    def _get_system_prompt(self) -> str:
        return """You are ImplementerAgent for Zaoya. Generate unified diff.

Output JSON:
{
  "id": "ps_001", "task_id": "task_001", "diff": "...", "touched_files": [...], "notes": "..."
}

Rules: Output ONLY valid JSON, proper diff format, ≤5 files, Zaoya.* functions, NO fetch/XHR/storage/eval."""

    def _get_output_type(self): from .models import PatchSet; return PatchSet

    def _build_user_message(self, inputs: Dict) -> str:
        task, files = inputs.get("task", {}), inputs.get("relevant_files", {})
        msg = f"# Task\n{json.dumps(task)}\n\n# Acceptance\n" + "\n".join(f"- {c}" for c in task.get("acceptance", []))
        for path, content in files.items():
            msg += f"\n## {path}\n```\n{content[:500]}\n```\n"
        return msg
```

### Task 3.4: Implement ReviewerAgent

```python
class ReviewerAgent(BaseAgent):
    def _get_system_prompt(self) -> str:
        return """You are ReviewerAgent for Zaoya. Review patch.

Output JSON:
{
  "decision": "approve" | "request_changes",
  "reasons": [...],
  "required_fixes": [...]
}

APPROVE if: all criteria met, validation passed, checks passed, no security issues.
REQUEST_CHANGES otherwise. NO fetch/XHR/storage/eval.

Output ONLY valid JSON."""

    def _get_output_type(self): from .models import ReviewReport; return ReviewReport

    def _build_user_message(self, inputs: Dict) -> str:
        return f"# Task\n{json.dumps(inputs.get('task', {}))}\n\n# Patch\n{json.dumps(inputs.get('patchset', {}))}\n\n# Validation\n{json.dumps(inputs.get('validation_report', {}))}\n\n# Checks\n{json.dumps(inputs.get('check_report', {}))}\n\nReview:"
```

### Task 3.5: Agent Factory

```python
def create_planner_agent(model="glm-4.7"): return PlannerAgent(model)
def create_implementer_agent(model="glm-4.7"): return ImplementerAgent(model)
def create_reviewer_agent(model="glm-4.7"): return ReviewerAgent(model)

planner = create_planner_agent()
implementer = create_implementer_agent()
reviewer = create_reviewer_agent()

__all__ = ["PlannerAgent", "ImplementerAgent", "ReviewerAgent", "planner", "implementer", "reviewer"]
```

---

## Acceptance Criteria

- PlannerAgent produces valid BuildGraph (<=15 tasks)
- ImplementerAgent produces valid unified diff (≤5 files)
- ReviewerAgent produces valid ReviewReport
- Tests cover agent output parsing

---

## Estimated Scope

**Complexity**: Medium
**Estimated Lines**: ~300-500
