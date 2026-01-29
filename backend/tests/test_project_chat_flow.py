import os
import sys
import unittest
import asyncio
import json
from pathlib import Path
from httpx import AsyncClient, ASGITransport

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.main import app


class ProjectChatFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["ZAOYA_INTERVIEW_MOCK"] = "1"
        os.environ["ZAOYA_DISABLE_INTENT_AI"] = "1"
        os.environ["ZAOYA_BYPASS_AUTH"] = "1"
        os.environ.setdefault("ZAOYA_INTERVIEW_STORAGE", "memory")

    def _run(self, coro):
        return asyncio.run(coro)

    def _parse_sse_payload(self, text: str) -> dict:
        for part in text.split("\n\n"):
            line = part.strip()
            if not line.startswith("data:"):
                continue
            data = line[len("data:") :].strip()
            if data == "[DONE]":
                continue
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                continue
        return {}

    def _build_answers(self, group: dict) -> list[dict]:
        answers: list[dict] = []
        for question in group.get("questions", []):
            question_id = question.get("id")
            if not question_id:
                continue
            question_type = question.get("type")
            options = question.get("options") or []
            if question_type in ("text", "date"):
                answers.append({"question_id": question_id, "raw_text": "Test"})
            elif question_type == "multi_select":
                selected = [options[0]["value"]] if options else ["skip"]
                answers.append(
                    {
                        "question_id": question_id,
                        "raw_text": "",
                        "selected_options": selected,
                    }
                )
            else:
                selected = [options[0]["value"]] if options else ["skip"]
                answers.append(
                    {
                        "question_id": question_id,
                        "raw_text": "",
                        "selected_options": selected,
                    }
                )
        return answers

    async def _exercise_flow(self) -> dict:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            project_id = "11111111-1111-4111-8111-111111111111"
            start_response = await client.post(
                f"/api/projects/{project_id}/chat",
                json={
                    "content": "I need a SaaS landing page for a new product launch",
                    "action": "start",
                },
            )
            if start_response.status_code != 200:
                raise AssertionError(start_response.text)
            start_payload = self._parse_sse_payload(start_response.text)
            next_action = start_payload.get("orchestrator", {}).get("next_action", {})
            self.assertEqual(start_payload.get("orchestrator", {}).get("mode"), "interview")

            group = None
            if next_action.get("type") == "ask_group":
                group = next_action.get("group")
            elif next_action.get("type") == "ask_followup":
                group = {"questions": next_action.get("questions", [])}

            if group:
                answers = self._build_answers(group)
                answer_response = await client.post(
                    f"/api/projects/{project_id}/chat",
                    json={"action": "answer", "answers": answers},
                )
                if answer_response.status_code != 200:
                    raise AssertionError(answer_response.text)
                answer_payload = self._parse_sse_payload(answer_response.text)
            else:
                answer_payload = start_payload

            answer_action = answer_payload.get("orchestrator", {}).get("next_action", {})
            if answer_action.get("type") == "finish":
                return answer_payload

            if answer_action.get("type") in ("ask_group", "ask_followup"):
                skip_response = await client.post(
                    f"/api/projects/{project_id}/chat",
                    json={"action": "skip"},
                )
                if skip_response.status_code != 200:
                    raise AssertionError(skip_response.text)
                _ = self._parse_sse_payload(skip_response.text)

            generate_response = await client.post(
                f"/api/projects/{project_id}/chat",
                json={"action": "generate_now"},
            )
            if generate_response.status_code != 200:
                raise AssertionError(generate_response.text)
            return self._parse_sse_payload(generate_response.text)

    def test_project_chat_flow_supports_actions(self) -> None:
        payload = self._run(self._exercise_flow())
        self.assertEqual(payload.get("orchestrator", {}).get("next_action", {}).get("type"), "finish")


if __name__ == "__main__":
    unittest.main()
