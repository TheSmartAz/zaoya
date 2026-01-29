"""Tailwind CSS generation helpers (critical CSS extraction)."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import logging

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT_DIR / "frontend" / "tailwind.config.js"
BACKUP_CONFIG = ROOT_DIR / "backend" / "tailwind.config.js"


def _find_tailwind_cli() -> list[str]:
    candidates = [
        ROOT_DIR / "node_modules" / ".bin" / "tailwindcss",
        ROOT_DIR / "frontend" / "node_modules" / ".bin" / "tailwindcss",
    ]
    for candidate in candidates:
        if candidate.exists():
            return [str(candidate)]
    return ["npx", "tailwindcss"]


def _resolve_config_path() -> Path | None:
    if DEFAULT_CONFIG.exists():
        return DEFAULT_CONFIG
    if BACKUP_CONFIG.exists():
        return BACKUP_CONFIG
    return None


def generate_tailwind_css(html: str) -> str:
    """Generate Tailwind CSS for the provided HTML content."""
    config_path = _resolve_config_path()
    if not config_path:
        logger.warning("Tailwind config not found; skipping CSS generation.")
        return ""

    html_content = html or ""
    try:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_css = temp_path / "input.css"
            content_html = temp_path / "content.html"
            output_css = temp_path / "output.css"

            input_css.write_text(
                "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n",
                encoding="utf-8",
            )
            content_html.write_text(html_content, encoding="utf-8")

            cmd = _find_tailwind_cli()
            cmd += [
                "-i",
                str(input_css),
                "-o",
                str(output_css),
                "--content",
                str(content_html),
                "--config",
                str(config_path),
                "--minify",
            ]

            subprocess.run(
                cmd,
                cwd=str(ROOT_DIR),
                check=True,
                capture_output=True,
                text=True,
            )

            return output_css.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Tailwind CSS generation failed: %s", exc)
        return ""
