"""Content Security Policy helpers for preview/publish."""

from __future__ import annotations

from app.services.template_renderer import get_runtime_script_hash


def build_preview_csp(api_origin: str) -> str:
    connect_src = api_origin if api_origin else "'self'"
    return "; ".join(
        [
            "default-src 'none'",
            "img-src 'self' data: blob: https:",
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com",
            f"connect-src {connect_src}",
            "font-src 'self' data:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
    )


def build_publish_csp(api_origin: str) -> str:
    connect_src = api_origin if api_origin else "'self'"
    runtime_hash = get_runtime_script_hash()
    return "; ".join(
        [
            "default-src 'none'",
            "img-src 'self' data: blob: https:",
            "style-src 'self' 'unsafe-inline'",
            f"script-src 'self' '{runtime_hash}'",
            f"connect-src {connect_src}",
            "font-src 'self' data:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
    )


def build_sim_csp(api_origin: str, report_uri: str | None = None) -> str:
    """CSP for publish simulation (allow embedding, otherwise strict)."""
    connect_src = api_origin if api_origin else "'self'"
    runtime_hash = get_runtime_script_hash()
    directives = [
        "default-src 'none'",
        "img-src 'self' data: blob: https:",
        "style-src 'self' 'unsafe-inline'",
        f"script-src 'self' '{runtime_hash}'",
        f"connect-src {connect_src}",
        "font-src 'self' data:",
        "base-uri 'self'",
        "form-action 'self'",
    ]
    if report_uri:
        directives.append(f"report-uri {report_uri}")
    return "; ".join(directives)
