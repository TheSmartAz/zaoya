"""Validation tools wrapping the existing validator pipeline."""

from __future__ import annotations

from app.services.validator import validate_html, validate_js_with_details
from .models import ValidationReport


class ValidateTools:
    async def run(
        self,
        html: str,
        js: str | None = None,
        *,
        html_path: str | None = None,
        js_path: str | None = None,
    ) -> ValidationReport:
        errors: list[str] = []
        warnings: list[str] = []
        js_valid = True
        error_details: list[dict] = []

        html_result = validate_html(html, path=html_path)
        normalized_html = None
        if html_result:
            errors.extend(html_result.get("errors", []))
            warnings.extend(html_result.get("warnings", []))
            normalized_html = html_result.get("normalized_html")
            error_details.extend(html_result.get("error_details", []) or [])

        if js:
            js_valid, js_errors, js_details = validate_js_with_details(js, path=js_path)
            errors.extend(js_errors)
            error_details.extend(js_details)

        return ValidationReport(
            ok=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            error_details=error_details,
            normalized_html=normalized_html,
            js_valid=js_valid,
        )
