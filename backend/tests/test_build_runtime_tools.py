import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.services.build_runtime.repo_tools import RepoTools
from app.services.build_runtime.validate_tools import ValidateTools
from app.services.build_runtime.check_tools import CheckTools
from app.services.build_runtime.snapshot_tools import SnapshotTools


class RepoToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "foo.txt").write_text("line1\nline2\n", encoding="utf-8")
        (self.root / "bar.py").write_text("print('hi')\n", encoding="utf-8")
        (self.root / "notes.txt").write_text("note\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_read_search_apply_patch(self) -> None:
        tools = RepoTools(self.root.as_posix())

        read_result = asyncio.run(tools.read("foo.txt", 1, 2))
        self.assertEqual(read_result, "line2\n")

        matches = asyncio.run(tools.search("*.txt"))
        self.assertIn("foo.txt", matches)
        self.assertIn("notes.txt", matches)

        diff = "\n".join(
            [
                "diff --git a/foo.txt b/foo.txt",
                "index 1111111..2222222 100644",
                "--- a/foo.txt",
                "+++ b/foo.txt",
                "@@ -1,2 +1,3 @@",
                " line1",
                "-line2",
                "+line2 updated",
                "+line3",
                "diff --git a/new.txt b/new.txt",
                "new file mode 100644",
                "--- /dev/null",
                "+++ b/new.txt",
                "@@ -0,0 +1,2 @@",
                "+hello",
                "+world",
                "",
            ]
        )

        result = asyncio.run(tools.apply_patch(diff))
        self.assertTrue(result["applied"])
        self.assertIn("foo.txt", result["touched"])
        self.assertIn("new.txt", result["touched"])

        updated = (self.root / "foo.txt").read_text(encoding="utf-8")
        self.assertEqual(updated, "line1\nline2 updated\nline3\n")
        created = (self.root / "new.txt").read_text(encoding="utf-8")
        self.assertEqual(created, "hello\nworld\n")


class ValidateToolsTests(unittest.TestCase):
    def test_validate_html_and_js(self) -> None:
        tools = ValidateTools()
        html_result = asyncio.run(tools.run("<script>alert(1)</script>"))
        self.assertFalse(html_result.ok)
        self.assertTrue(html_result.errors)
        self.assertTrue(html_result.normalized_html)

        js_result = asyncio.run(tools.run("<div></div>", "fetch('x')"))
        self.assertFalse(js_result.js_valid)
        self.assertTrue(js_result.errors)


class CheckToolsTests(unittest.TestCase):
    def test_missing_scripts_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frontend = root / "frontend"
            frontend.mkdir(parents=True, exist_ok=True)
            (frontend / "package.json").write_text(
                '{"name":"frontend","scripts":{"build":"echo build"}}',
                encoding="utf-8",
            )
            tools = CheckTools(root.as_posix())
            result = asyncio.run(tools.typecheck())
            self.assertTrue(result["ok"])
            self.assertEqual(result["output"], "skipped")


class SnapshotToolsTests(unittest.TestCase):
    def test_snapshot_create_restore(self) -> None:
        svc = AsyncMock()
        svc.create.return_value = "snap-123"
        svc.restore.return_value = True
        with patch("app.services.build_runtime.snapshot_tools.get_snapshot_service", return_value=svc):
            tools = SnapshotTools("proj-1")
            created = asyncio.run(tools.create("reason"))
            self.assertEqual(created, "snap-123")
            restored = asyncio.run(tools.restore("snap-123"))
            self.assertTrue(restored)

    def test_snapshot_restore_failure(self) -> None:
        svc = AsyncMock()
        svc.restore.side_effect = RuntimeError("boom")
        with patch("app.services.build_runtime.snapshot_tools.get_snapshot_service", return_value=svc):
            tools = SnapshotTools("proj-1")
            restored = asyncio.run(tools.restore("snap-123"))
            self.assertFalse(restored)


if __name__ == "__main__":
    unittest.main()
