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


class ChatIntentTests(unittest.TestCase):
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

    async def _exercise_chat(self, use_db: bool) -> tuple[dict, dict, str]:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            project_id = "11111111-1111-4111-8111-111111111111"
            if use_db:
                project_response = await client.post(
                    "/api/projects",
                    json={"name": "Interview Test Project"},
                )
                if project_response.status_code != 200:
                    raise AssertionError(project_response.text)
                project_id = project_response.json()["id"]

            response = await client.post(
                f"/api/projects/{project_id}/chat",
                json={"content": "We need a birthday invitation page", "action": "start"},
            )
            if response.status_code != 200:
                raise AssertionError(response.text)
            start_payload = self._parse_sse_payload(response.text)

            followup = await client.post(
                f"/api/projects/{project_id}/chat",
                json={"action": "generate_now"},
            )
            if followup.status_code != 200:
                raise AssertionError(followup.text)
            followup_payload = self._parse_sse_payload(followup.text)
            return start_payload, followup_payload, response.text

    def test_project_chat_starts_interview_stream(self) -> None:
        use_db = os.environ.get("ZAOYA_INTERVIEW_STORAGE") != "memory"
        start_payload, followup_payload, text = self._run(self._exercise_chat(use_db))
        self.assertIn("data:", text)
        self.assertIn("[DONE]", text)
        self.assertEqual(start_payload.get("orchestrator", {}).get("mode"), "interview")
        self.assertEqual(start_payload.get("state", {}).get("detected_intent"), "event-invitation")
        self.assertEqual(
            followup_payload.get("orchestrator", {}).get("next_action", {}).get("type"),
            "finish",
        )


if __name__ == "__main__":
    unittest.main()
