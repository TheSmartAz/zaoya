"""Repository tools for reading, searching, and patching files."""

from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


class RepoTools:
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()

    async def read(self, path: str, start_line: int = 0, end_line: int | None = None) -> str:
        full_path = (self.project_path / path).resolve()
        if not self._is_within_project(full_path):
            raise ValueError("Path escapes project root")
        content = full_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        start = max(start_line, 0)
        end = min(end_line, len(lines)) if end_line is not None else None
        return "".join(lines[start:end])

    async def search(self, query: str) -> List[str]:
        matches: List[str] = []
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__"}]
            for filename in files:
                if fnmatch.fnmatch(filename, query):
                    rel = os.path.relpath(os.path.join(root, filename), self.project_path)
                    matches.append(rel)
        return matches[:50]

    async def apply_patch(self, diff: str) -> Dict:
        result = {"applied": False, "touched": [], "errors": []}
        try:
            file_hunks = self._parse_diff(diff)
        except ValueError as exc:
            result["errors"].append(str(exc))
            return result

        for file_path, payload in file_hunks.items():
            try:
                full_path = (self.project_path / file_path).resolve()
                if not self._is_within_project(full_path):
                    result["errors"].append(f"Invalid path: {file_path}")
                    continue

                if payload.get("delete"):
                    if full_path.exists():
                        full_path.unlink()
                        result["touched"].append(file_path)
                    continue

                original = ""
                if full_path.exists():
                    original = full_path.read_text(encoding="utf-8")
                elif not payload.get("new_file"):
                    result["errors"].append(f"File not found: {file_path}")
                    continue

                new_content = self._apply_hunks(original, payload["hunks"])
                if new_content != original or not full_path.exists():
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(new_content, encoding="utf-8")
                    result["touched"].append(file_path)
            except Exception as exc:
                result["errors"].append(f"{file_path}: {exc}")

        result["applied"] = len(result["errors"]) == 0
        return result

    def _parse_diff(self, diff: str) -> Dict[str, Dict]:
        lines = diff.splitlines()
        files: Dict[str, Dict] = {}
        current_file: str | None = None
        current_old: str | None = None
        for line in lines:
            if line.startswith("diff --git"):
                current_file = None
                current_old = None
                continue

            if line.startswith("--- "):
                current_old = line[4:].split("\t")[0]
                continue

            if line.startswith("+++ "):
                new_path = line[4:].split("\t")[0]
                if new_path == "/dev/null":
                    if not current_old:
                        raise ValueError("Malformed diff: delete without original path")
                    path = current_old.replace("a/", "", 1)
                    files[path] = {"hunks": [], "delete": True, "new_file": False}
                    current_file = path
                    continue

                path = new_path.replace("b/", "", 1)
                files[path] = {
                    "hunks": [],
                    "delete": False,
                    "new_file": current_old == "/dev/null",
                }
                current_file = path
                continue

            if line.startswith("@@ "):
                if not current_file:
                    raise ValueError("Malformed diff: hunk without file header")
                match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
                if not match:
                    raise ValueError("Malformed diff: invalid hunk header")
                old_start = int(match.group(1))
                old_count = int(match.group(2) or 1)
                new_start = int(match.group(3))
                new_count = int(match.group(4) or 1)
                hunk = {
                    "old_start": old_start,
                    "old_count": old_count,
                    "new_start": new_start,
                    "new_count": new_count,
                    "lines": [],
                }
                files[current_file]["hunks"].append(hunk)
                continue

            if current_file and files[current_file]["hunks"]:
                if line.startswith((" ", "+", "-")):
                    files[current_file]["hunks"][-1]["lines"].append((line[0], line[1:]))
                elif line.startswith("\\ No newline at end of file"):
                    continue

        return files

    def _apply_hunks(self, original: str, hunks: List[Dict]) -> str:
        lines = original.splitlines(keepends=True)
        result: List[str] = []
        idx = 0

        for hunk in hunks:
            start_index = max(hunk["old_start"] - 1, 0)
            if start_index < idx:
                raise ValueError("Overlapping hunks detected")
            result.extend(lines[idx:start_index])
            idx = start_index

            for tag, text in hunk["lines"]:
                if tag == " ":
                    if idx >= len(lines) or lines[idx].rstrip("\n") != text:
                        raise ValueError("Hunk context mismatch")
                    result.append(lines[idx])
                    idx += 1
                elif tag == "-":
                    if idx >= len(lines) or lines[idx].rstrip("\n") != text:
                        raise ValueError("Hunk removal mismatch")
                    idx += 1
                elif tag == "+":
                    if text.endswith("\n"):
                        result.append(text)
                    else:
                        result.append(text + "\n")

        result.extend(lines[idx:])
        return "".join(result)

    def _is_within_project(self, full_path: Path) -> bool:
        try:
            full_path.relative_to(self.project_path)
            return True
        except ValueError:
            return False
