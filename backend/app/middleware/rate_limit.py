"""Global rate limiting middleware."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware.

    Limits requests per IP to prevent abuse.
    Use a proper Redis-based implementation in production.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        requests_per_hour: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests = defaultdict(list)
        self.hour_requests = defaultdict(list)
        self.lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health", "/api/health"]:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = datetime.utcnow()

        async with self.lock:
            # Clean old entries
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)

            self.minute_requests[client_ip] = [
                ts for ts in self.minute_requests[client_ip]
                if ts > minute_ago
            ]
            self.hour_requests[client_ip] = [
                ts for ts in self.hour_requests[client_ip]
                if ts > hour_ago
            ]

            # Check minute limit
            if len(self.minute_requests[client_ip]) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Window": "60",
                    },
                )

            # Check hour limit
            if len(self.hour_requests[client_ip]) >= self.requests_per_hour:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Try again later.",
                    headers={
                        "Retry-After": "3600",
                        "X-RateLimit-Limit": str(self.requests_per_hour),
                        "X-RateLimit-Window": "3600",
                    },
                )

            # Record this request
            self.minute_requests[client_ip].append(now)
            self.hour_requests[client_ip].append(now)

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request, handling proxies."""
        # Check for forwarded headers (in production, verify these)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"
