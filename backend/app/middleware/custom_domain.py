"""Middleware to detect and handle custom domain requests."""

from typing import List, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class CustomDomainMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and handle custom domain requests.

    SECURITY: Only trusts X-Custom-Domain header when:
    1. Valid X-Zaoya-Edge-Secret is present, AND
    2. (Optional) Request is from allowed edge IP

    When Caddy proxies a request, it adds:
    - X-Custom-Domain: The original host header (e.g., example.com)
    - X-Zaoya-Edge-Secret: Shared secret for authentication
    - X-Real-IP: The original client IP
    - X-Forwarded-Proto: The original protocol (https)
    """

    ZAOYA_DOMAINS = ["zaoya.app", "localhost", "127.0.0.1"]

    def __init__(
        self,
        app,
        edge_secret: Optional[str] = None,
        allowed_edge_ips: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.edge_secret = edge_secret or settings.zaoya_edge_secret
        self.allowed_edge_ips = allowed_edge_ips or settings.allowed_edge_ips or []

    async def dispatch(self, request: Request, call_next):
        custom_domain: Optional[str] = None
        is_custom_domain = False

        # Only trust X-Custom-Domain if edge secret is valid
        provided_secret = request.headers.get("X-Zaoya-Edge-Secret")
        header_domain = request.headers.get("X-Custom-Domain")

        if header_domain and self._is_valid_edge_request(request, provided_secret):
            # Normalize domain
            normalized = header_domain.lower().strip().rstrip(".")

            # Check if this is actually a custom domain (not our own)
            is_custom_domain = not any(
                normalized.endswith(d) or normalized == d for d in self.ZAOYA_DOMAINS
            )

            if is_custom_domain:
                custom_domain = normalized

        # Attach to request state for downstream handlers
        request.state.custom_domain = custom_domain
        request.state.is_custom_domain = is_custom_domain

        response = await call_next(request)
        return response

    def _is_valid_edge_request(
        self, request: Request, provided_secret: Optional[str]
    ) -> bool:
        """Validate the request is from our edge server."""
        # Check secret
        if not self.edge_secret or provided_secret != self.edge_secret:
            return False

        # Optional: Check source IP
        if self.allowed_edge_ips:
            client_ip = request.client.host if request.client else None
            forwarded_for = (
                request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            )
            real_ip = request.headers.get("X-Real-IP")

            request_ip = real_ip or forwarded_for or client_ip
            if request_ip not in self.allowed_edge_ips:
                return False

        return True
