import asyncio
import unittest
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID
from unittest.mock import patch

from app.services.build_runtime.events import BuildEventType
from app.services.build_runtime.multi_task_orchestrator import BuildSession, MultiTaskOrchestrator
from app.services.build_runtime.planner import PageSpec


class VersionCardEmissionTests(unittest.TestCase):
    def test_build_stream_emits_version_card(self) -> None:
        orchestrator = MultiTaskOrchestrator()
        session_id = "session-1"
        project_id = "11111111-1111-4111-8111-111111111111"
        user_id = "22222222-2222-4222-8222-222222222222"
        page = PageSpec(id="home", name="Home", path="/", is_main=True)
        session = BuildSession(
            id=session_id,
            project_id=project_id,
            user_id=user_id,
            pages=[page],
        )
        orchestrator.sessions[session_id] = session

        version_id = UUID("33333333-3333-4333-8333-333333333333")
        home_page_id = "44444444-4444-4444-8444-444444444444"

        async def fake_generate_page(self, session, page, product_doc, order):
            session.completed_pages.append(page.id)
            session.page_html[page.id] = "<html></html>"
            yield self.emitter.task_done(f"page-{page.id}", "done")

        async def fake_complete_project_tasks(self, session):
            return []

        @asynccontextmanager
        async def fake_session_ctx():
            yield None

        class FakeVersionService:
            def __init__(self, _db):
                pass

            async def create_version_from_project(self, *args, **kwargs):
                return SimpleNamespace(
                    id=version_id,
                    created_at=datetime.now(timezone.utc),
                    change_summary={},
                    validation_status="passed",
                    is_pinned=False,
                    branch_label=None,
                )

            async def get_version_snapshot(self, *args, **kwargs):
                return {
                    "pages": [
                        {
                            "id": home_page_id,
                            "name": "Home",
                            "path": "/",
                            "is_home": True,
                        }
                    ]
                }

        async def collect_events():
            events = []
            async for event in orchestrator.stream_progress(session_id, SimpleNamespace()):
                events.append(event)
            return events

        with patch.object(MultiTaskOrchestrator, "_generate_page", new=fake_generate_page), \
            patch.object(MultiTaskOrchestrator, "_complete_project_tasks", new=fake_complete_project_tasks), \
            patch("app.services.build_runtime.multi_task_orchestrator.AsyncSessionLocal", fake_session_ctx), \
            patch("app.services.build_runtime.multi_task_orchestrator.VersionService", FakeVersionService):
            events = asyncio.run(collect_events())

        version_cards = [
            event
            for event in events
            if event.type == BuildEventType.CARD and event.card_type == "version"
        ]
        self.assertEqual(len(version_cards), 1)


if __name__ == "__main__":
    unittest.main()
