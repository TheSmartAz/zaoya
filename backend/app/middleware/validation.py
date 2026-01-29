"""Request size validation middleware."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Limit request body size to prevent DoS attacks.

    Rejects requests larger than the configured maximum size.
    """

    def __init__(self, app, max_size_mb: int = 10):
        super().__init__(app)
        self.max_size_bytes = max_size_mb * 1024 * 1024

    async def dispatch(self, request: Request, call_next):
        # Check content-length header first
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Request too large. Maximum size is {self.max_size_bytes // (1024 * 1024)}MB.",
                    )
            except ValueError:
                pass

        response = await call_next(request)
        return response
