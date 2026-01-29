import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.services.build_runtime.agents import ImplementerAgent, PlannerAgent
from app.services.ai_service import LLMResponse, LLMUsage


class PlannerAgentTests(unittest.TestCase):
    def test_parses_code_fenced_json(self) -> None:
        response = """```json
{
  "tasks": [
    {
      "id": "task_001",
      "title": "Create header",
      "goal": "Add a header",
      "acceptance": ["Header exists"],
      "depends_on": [],
      "files_expected": ["frontend/src/components/Header.tsx"],
      "status": "todo"
    },
    {
      "id": "task_002",
      "title": "Create hero",
      "goal": "Add hero",
      "acceptance": ["Hero exists"],
      "depends_on": [],
      "files_expected": ["frontend/src/components/Hero.tsx"],
      "status": "todo"
    },
    {
      "id": "task_003",
      "title": "Create features",
      "goal": "Add features",
      "acceptance": ["Features exist"],
      "depends_on": [],
      "files_expected": ["frontend/src/components/Features.tsx"],
      "status": "todo"
    },
    {
      "id": "task_004",
      "title": "Create CTA",
      "goal": "Add CTA",
      "acceptance": ["CTA exists"],
      "depends_on": [],
      "files_expected": ["frontend/src/components/Cta.tsx"],
      "status": "todo"
    },
    {
      "id": "task_005",
      "title": "Create footer",
      "goal": "Add footer",
      "acceptance": ["Footer exists"],
      "depends_on": [],
      "files_expected": ["frontend/src/components/Footer.tsx"],
      "status": "todo"
    }
  ],
  "notes": "ok"
}
```"""
        llm = LLMResponse(content=response, usage=LLMUsage(1, 2, 3), model="glm-4.7")
        with patch("app.services.ai_service.chat_complete", new=AsyncMock(return_value=llm)):
            agent = PlannerAgent()
            result = asyncio.run(agent.run(brief={}, build_plan={}, product_doc={}))

        self.assertIn("tasks", result.output)
        self.assertEqual(result.output["tasks"][0]["id"], "task_001")
        self.assertEqual(result.tokens_used, 3)
        self.assertEqual(result.token_usage.total_tokens, 3)

    def test_invalid_json_raises(self) -> None:
        llm = LLMResponse(content="nope", usage=LLMUsage(), model="glm-4.7")
        with patch("app.services.ai_service.chat_complete", new=AsyncMock(return_value=llm)):
            agent = PlannerAgent()
            with self.assertRaises(ValueError):
                asyncio.run(agent.run(brief={}, build_plan={}, product_doc={}))


class ImplementerAgentTests(unittest.TestCase):
    def test_parses_plain_json(self) -> None:
        response = """
{
  "id": "ps_001",
  "task_id": "task_001",
  "diff": "diff --git a/a.txt b/a.txt",
  "touched_files": ["a.txt"],
  "notes": "ok"
}
""".strip()
        llm = LLMResponse(content=response, usage=LLMUsage(4, 5, 9), model="glm-4.7")
        with patch("app.services.ai_service.chat_complete", new=AsyncMock(return_value=llm)):
            agent = ImplementerAgent()
            result = asyncio.run(agent.run(task={"id": "task_001"}, relevant_files={}))

        self.assertEqual(result.output["id"], "ps_001")
        self.assertEqual(result.output["task_id"], "task_001")
        self.assertEqual(result.tokens_used, 9)


if __name__ == "__main__":
    unittest.main()
