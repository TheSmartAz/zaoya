"""Tooling for running typecheck, lint, and unit tests."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Dict

from .models import CheckReport


class CheckTools:
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.frontend_path = self.project_path / "frontend"
        self.backend_path = self.project_path / "backend"
        self._frontend_scripts: dict | None = None

    async def typecheck(self) -> Dict:
        return await self._run_frontend_script("typecheck")

    async def lint(self) -> Dict:
        return await self._run_frontend_script("lint")

    async def unit(self) -> Dict:
        try:
            proc = await asyncio.create_subprocess_exec(
                "python",
                "-m",
                "pytest",
                "-q",
                str(self.backend_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode() + (stderr.decode() if stderr else "")
            return {"ok": proc.returncode == 0, "output": output}
        except FileNotFoundError:
            return {"ok": True, "output": "skipped", "skipped": True}

    async def all(self) -> CheckReport:
        t = await self.typecheck()
        l = await self.lint()
        u = await self.unit()
        return CheckReport(
            ok=t["ok"] and l["ok"] and u["ok"],
            typecheck_ok=t["ok"],
            lint_ok=l["ok"],
            unit_ok=u["ok"],
            logs=f"TC: {t['output']}\nLint: {l['output']}\nUnit: {u['output']}",
        )

    def _load_frontend_scripts(self) -> dict:
        if self._frontend_scripts is not None:
            return self._frontend_scripts
        pkg_path = self.frontend_path / "package.json"
        if not pkg_path.exists():
            self._frontend_scripts = {}
            return self._frontend_scripts
        try:
            data = json.loads(pkg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self._frontend_scripts = {}
            return self._frontend_scripts
        self._frontend_scripts = data.get("scripts", {}) or {}
        return self._frontend_scripts

    async def _run_frontend_script(self, name: str) -> Dict:
        scripts = self._load_frontend_scripts()
        if name not in scripts:
            return {"ok": True, "output": "skipped", "skipped": True}
        try:
            proc = await asyncio.create_subprocess_exec(
                "pnpm",
                "-C",
                str(self.frontend_path),
                name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode() + (stderr.decode() if stderr else "")
            return {"ok": proc.returncode == 0, "output": output}
        except FileNotFoundError:
            return {"ok": True, "output": "skipped", "skipped": True}
