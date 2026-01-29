"""Error handling middleware to prevent information leakage."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback
import logging

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Catch and handle errors gracefully.

    Logs full error details server-side but returns generic
    messages to clients to prevent information leakage.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the full error for debugging
            logger.error(f"Error handling {request.url}: {e}")
            logger.error(traceback.format_exc())

            # Return generic error to client
            # In production, don't expose error details
            status = getattr(e, "status_code", 500)

            # Some built-in exceptions have detail attribute
            detail = getattr(e, "detail", None)

            if status < 500:
                # Client errors (4xx) can return their message
                return JSONResponse(
                    status_code=status,
                    content={"detail": detail or "Bad request"},
                )

            # Server errors (5xx) get generic message
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
