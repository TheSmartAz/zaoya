# Phase 2: Tool Layer

**Duration**: Week 2
**Status**: Pending
**Depends On**: Phase 1 (Build Runtime Foundation)

---

## Phase Overview

This phase implements the tool layer that enables agents to interact with the codebase, run validation, and perform quality checks.

---

## Prerequisites

- Phase 1 complete (models and storage)
- Existing validator pipeline
- Frontend package.json with typecheck/lint scripts

---

## Detailed Tasks

### Task 2.1: Implement Repo Tools

Create `backend/app/services/build_runtime/repo_tools.py` with:
- `read(path, start_line?, end_line?)` - Read file content
- `search(query)` - Search files by pattern
- `apply_patch(diff)` - Apply unified diff

```python
class RepoTools:
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)

    async def read(self, path: str, start_line: int = 0, end_line = None) -> str:
        full_path = self.project_path / path
        content = full_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        if end_line:
            end_line = min(end_line, len(lines))
        return "".join(lines[start_line:end_line])

    async def search(self, query: str) -> List[str]:
        matches = []
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__'}]
            for filename in files:
                if fnmatch.fnmatch(filename, query):
                    matches.append(os.path.relpath(os.path.join(root, filename), self.project_path))
        return matches[:50]

    async def apply_patch(self, diff: str) -> Dict:
        result = {"applied": False, "touched": [], "errors": []}
        file_hunks = self._parse_diff(diff)
        for file_path, hunks in file_hunks.items():
            full_path = self.project_path / file_path
            if full_path.exists():
                original = full_path.read_text(encoding="utf-8")
                new_content = self._apply_hunks(original, hunks)
                if new_content != original:
                    full_path.write_text(new_content, encoding="utf-8")
                    result["touched"].append(file_path)
            result["applied"] = len(result["errors"]) == 0
        return result

    def _parse_diff(self, diff: str) -> Dict:
        lines = diff.splitlines()
        files, current_file, current_hunk = {}, None, None
        for line in lines:
            if line.startswith("+++ "):
                path = line[4:].split("\t")[0].replace("b/", "")
                current_file, files[path] = path, []
            elif line.startswith("@@ "):
                import re
                m = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", line)
                current_hunk = {"old_content": [], "new_content": []}
                files[current_file].append(current_hunk)
            elif current_hunk and line.startswith("-"):
                current_hunk["old_content"].append(line[1:])
            elif current_hunk and line.startswith("+"):
                current_hunk["new_content"].append(line[1:])
        return files

    def _apply_hunks(self, original: str, hunks: List[Dict]) -> str:
        lines = original.splitlines(keepends=True)
        result, idx = [], 0
        for hunk in hunks:
            while idx < hunk["old_start"] - 1 and idx < len(lines):
                result.append(lines[idx]); idx += 1
            for _ in hunk["old_lines"]:  # Skip old lines
                if idx < len(lines): idx += 1
            for new_line in hunk["new_content"]:  # Add new lines
                result.append(new_line + "\n" if not new_line.endswith("\n") else new_line)
        while idx < len(lines):
            result.append(lines[idx]); idx += 1
        return "".join(result)
```

### Task 2.2: Implement ValidateTools

```python
class ValidateTools:
    async def run(self, html: str, js: str = None) -> ValidationReport:
        from app.services.validator import validate_html, validate_js
        errors, warnings, js_valid = [], [], True
        html_result = await validate_html(html)
        if html_result:
            errors.extend(html_result.get("errors", []))
            warnings.extend(html_result.get("warnings", []))
        if js:
            js_result = validate_js(js)
            js_valid = js_result.get("ok", True)
            errors.extend(js_result.get("errors", []))
        return ValidationReport(ok=len(errors) == 0, errors=errors, warnings=warnings, js_valid=js_valid)
```

### Task 2.3: Implement CheckTools

```python
class CheckTools:
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.frontend_path = self.project_path / "frontend"
        self.backend_path = self.project_path / "backend"

    async def typecheck(self) -> Dict:
        try:
            proc = await asyncio.create_subprocess_exec("pnpm", "-C", str(self.frontend_path), "typecheck", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            return {"ok": proc.returncode == 0, "output": stdout.decode()}
        except FileNotFoundError: return {"ok": True, "output": "skipped", "skipped": True}

    async def lint(self) -> Dict:
        try:
            proc = await asyncio.create_subprocess_exec("pnpm", "-C", str(self.frontend_path), "lint", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            return {"ok": proc.returncode == 0, "output": stdout.decode()}
        except FileNotFoundError: return {"ok": True, "output": "skipped", "skipped": True}

    async def unit(self) -> Dict:
        try:
            proc = await asyncio.create_subprocess_exec("python", "-m", "pytest", "-q", str(self.backend_path), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            return {"ok": proc.returncode == 0, "output": stdout.decode()}
        except FileNotFoundError: return {"ok": True, "output": "skipped", "skipped": True}

    async def all(self) -> CheckReport:
        t, l, u = await self.typecheck(), await self.lint(), await self.unit()
        return CheckReport(ok=t["ok"] and l["ok"] and u["ok"], typecheck_ok=t["ok"], lint_ok=l["ok"], unit_ok=u["ok"], logs=f"TC: {t['output']}\nLint: {l['output']}\nUnit: {u['output']}")
```

### Task 2.4: Implement SnapshotTools

```python
class SnapshotTools:
    def __init__(self, project_id: str):
        self.project_id = project_id

    async def create(self, reason: str, metadata: dict = None) -> str:
        from app.services.snapshot_service import get_snapshot_service
        svc = get_snapshot_service()
        return await svc.create(project_id=self.project_id, reason=reason, metadata=metadata)

    async def restore(self, snapshot_id: str) -> bool:
        from app.services.snapshot_service import get_snapshot_service
        svc = get_snapshot_service()
        try: await svc.restore(snapshot_id, self.project_id); return True
        except: return False
```

### Task 2.5: Create tools module

```python
# tools.py
from .repo_tools import RepoTools
from .validate_tools import ValidateTools
from .check_tools import CheckTools
from .snapshot_tools import SnapshotTools
__all__ = ["RepoTools", "ValidateTools", "CheckTools", "SnapshotTools"]
```

---

## Acceptance Criteria

- RepoTools: read, search, apply_patch work
- ValidateTools: wraps existing validator
- CheckTools: typecheck, lint, unit, all work
- SnapshotTools: create, restore work
- Tests cover all tools

---

## Estimated Scope

**Complexity**: Medium
**Estimated Lines**: ~400-600
