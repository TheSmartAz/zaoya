import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.services.build_runtime.models import BuildState, BuildGraph, TaskStatus, ReviewDecision, BuildPhase
from app.services.build_runtime.orchestrator import BuildOrchestrator


class _FakeStorage:
    def __init__(self, state: BuildState):
        self.state = state

    async def get(self, build_id: str):
        return self.state if self.state.build_id == build_id else None

    async def save(self, state: BuildState):
        self.state = state

    async def create(self, state: BuildState):
        self.state = state


class OrchestratorPlanTests(unittest.TestCase):
    def test_plan_step_creates_graph_and_selects_task(self) -> None:
        build_id = "00000000-0000-0000-0000-000000000001"
        state = BuildState(
            build_id=build_id,
            project_id="00000000-0000-0000-0000-000000000010",
            user_id="00000000-0000-0000-0000-000000000011",
        )
        storage = _FakeStorage(state)
        planner_output = {
            "tasks": [
                {
                    "id": "task_001",
                    "title": "First",
                    "goal": "Do it",
                    "acceptance": ["Done"],
                    "depends_on": [],
                    "files_expected": ["frontend/src/App.tsx"],
                    "status": "todo",
                },
                {
                    "id": "task_002",
                    "title": "Second",
                    "goal": "Do it too",
                    "acceptance": ["Done"],
                    "depends_on": [],
                    "files_expected": ["frontend/src/App.tsx"],
                    "status": "todo",
                },
                {
                    "id": "task_003",
                    "title": "Third",
                    "goal": "Another",
                    "acceptance": ["Done"],
                    "depends_on": [],
                    "files_expected": ["frontend/src/App.tsx"],
                    "status": "todo",
                },
                {
                    "id": "task_004",
                    "title": "Fourth",
                    "goal": "Another",
                    "acceptance": ["Done"],
                    "depends_on": [],
                    "files_expected": ["frontend/src/App.tsx"],
                    "status": "todo",
                },
                {
                    "id": "task_005",
                    "title": "Fifth",
                    "goal": "Another",
                    "acceptance": ["Done"],
                    "depends_on": [],
                    "files_expected": ["frontend/src/App.tsx"],
                    "status": "todo",
                },
            ],
            "notes": "ok",
        }
        planner = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(output=planner_output)))

        orchestrator = BuildOrchestrator(storage=storage, planner=planner)
        result = asyncio.run(orchestrator.step(build_id, mode="plan_only"))

        self.assertIsNotNone(result.build_graph)
        self.assertEqual(result.current_task_id, "task_001")
        self.assertEqual(result.phase.value, "implementing")
        self.assertEqual(result.build_graph.tasks[0].status, TaskStatus.DOING)


class OrchestratorReviewTests(unittest.TestCase):
    def test_review_approve_marks_done(self) -> None:
        build_id = "00000000-0000-0000-0000-000000000101"
        state = BuildState(
            build_id=build_id,
            project_id="00000000-0000-0000-0000-000000000110",
            user_id="00000000-0000-0000-0000-000000000111",
            phase=BuildPhase.REVIEWING,
            build_graph=BuildGraph(
                tasks=[
                    {
                        "id": "task_001",
                        "title": "First",
                        "goal": "Do it",
                        "acceptance": ["Done"],
                        "depends_on": [],
                        "files_expected": [],
                        "status": "doing",
                    },
                    {
                        "id": "task_002",
                        "title": "Second",
                        "goal": "Done",
                        "acceptance": ["Done"],
                        "depends_on": [],
                        "files_expected": [],
                        "status": "done",
                    },
                    {
                        "id": "task_003",
                        "title": "Third",
                        "goal": "Done",
                        "acceptance": ["Done"],
                        "depends_on": [],
                        "files_expected": [],
                        "status": "done",
                    },
                    {
                        "id": "task_004",
                        "title": "Fourth",
                        "goal": "Done",
                        "acceptance": ["Done"],
                        "depends_on": [],
                        "files_expected": [],
                        "status": "done",
                    },
                    {
                        "id": "task_005",
                        "title": "Fifth",
                        "goal": "Done",
                        "acceptance": ["Done"],
                        "depends_on": [],
                        "files_expected": [],
                        "status": "done",
                    },
                ]
            ),
            current_task_id="task_001",
        )
        storage = _FakeStorage(state)
        reviewer_output = {
            "decision": "approve",
            "reasons": ["Looks good"],
            "required_fixes": [],
        }
        reviewer = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(output=reviewer_output)))

        orchestrator = BuildOrchestrator(storage=storage, reviewer=reviewer)
        result = asyncio.run(orchestrator.step(build_id, mode="auto"))

        self.assertEqual(result.last_review.decision, ReviewDecision.APPROVE)
        self.assertEqual(result.build_graph.tasks[0].status, TaskStatus.DONE)
        self.assertEqual(result.phase.value, "ready")
        self.assertIsNotNone(result.completed_at)


if __name__ == "__main__":
    unittest.main()
