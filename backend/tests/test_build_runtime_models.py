import unittest
from pydantic import ValidationError

from app.services.build_runtime.models import BuildGraph, Task, BuildState, AgentUsage, TokenUsage


def _task(task_id: str, status: str = "todo", depends=None, files=None):
    return {
        "id": task_id,
        "title": f"Title {task_id}",
        "goal": "Do it",
        "acceptance": ["Done"],
        "depends_on": depends or [],
        "files_expected": files or [],
        "status": status,
    }


class BuildGraphValidationTests(unittest.TestCase):
    def test_single_task_allowed(self) -> None:
        data = {"tasks": [_task("task_001")], "notes": ""}
        graph = BuildGraph.model_validate(data)
        self.assertEqual(len(graph.tasks), 1)

    def test_task_count_too_high(self) -> None:
        data = {"tasks": [_task(f"task_{i:03d}") for i in range(16)], "notes": ""}
        with self.assertRaises(ValidationError):
            BuildGraph.model_validate(data)

    def test_duplicate_task_ids(self) -> None:
        tasks = [_task("task_001") for _ in range(5)]
        data = {"tasks": tasks, "notes": ""}
        with self.assertRaises(ValidationError):
            BuildGraph.model_validate(data)

    def test_unknown_dependency(self) -> None:
        tasks = [_task(f"task_{i:03d}") for i in range(5)]
        tasks[0]["depends_on"] = ["task_999"]
        data = {"tasks": tasks, "notes": ""}
        with self.assertRaises(ValidationError):
            BuildGraph.model_validate(data)

    def test_files_expected_limit(self) -> None:
        files = [f"file_{i}.txt" for i in range(6)]
        with self.assertRaises(ValidationError):
            Task.model_validate(_task("task_001", files=files))

    def test_total_token_usage(self) -> None:
        state = BuildState(
            build_id="00000000-0000-0000-0000-000000000001",
            project_id="00000000-0000-0000-0000-000000000002",
            user_id="00000000-0000-0000-0000-000000000003",
        )
        state.agent_usage = [
            AgentUsage(
                agent="PlannerAgent",
                model="m1",
                usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            ),
            AgentUsage(
                agent="ImplementerAgent",
                model="m2",
                usage=TokenUsage(prompt_tokens=20, completion_tokens=10, total_tokens=30),
            ),
        ]
        totals = state.total_token_usage()
        self.assertEqual(totals.prompt_tokens, 30)
        self.assertEqual(totals.completion_tokens, 15)
        self.assertEqual(totals.total_tokens, 45)


if __name__ == "__main__":
    unittest.main()
