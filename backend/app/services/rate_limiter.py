"""Rate limiting service for API protection."""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional
import asyncio


class RateLimiter:
    """Simple in-memory rate limiter (use Redis in production)."""

    def __init__(self):
        self.attempts = defaultdict(list)
        self.lock = asyncio.Lock()

    async def is_limited(
        self,
        identifier: str,
        max_attempts: int = 10,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if the identifier has exceeded the rate limit.

        Args:
            identifier: Unique identifier (e.g., "ip:public_id" or "user_id:action")
            max_attempts: Maximum allowed attempts in the window
            window_seconds: Time window in seconds

        Returns:
            True if rate limited, False if allowed
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        async with self.lock:
            # Clean old entries outside the window
            self.attempts[identifier] = [
                ts for ts in self.attempts[identifier]
                if ts > window_start
            ]

            # Check if limit exceeded
            if len(self.attempts[identifier]) >= max_attempts:
                return True

            # Record this attempt
            self.attempts[identifier].append(now)
            return False

    async def check_and_record(
        self,
        identifier: str,
        max_attempts: int = 10,
        window_seconds: int = 60
    ) -> tuple[bool, int]:
        """
        Check rate limit and record attempt if allowed.

        Returns:
            Tuple of (is_limited, remaining_attempts)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        async with self.lock:
            # Clean old entries
            self.attempts[identifier] = [
                ts for ts in self.attempts[identifier]
                if ts > window_start
            ]

            current_count = len(self.attempts[identifier])

            if current_count >= max_attempts:
                return True, 0

            # Record this attempt
            self.attempts[identifier].append(now)
            return False, max_attempts - current_count - 1

    async def reset(self, identifier: str) -> None:
        """Reset rate limit for a specific identifier."""
        async with self.lock:
            self.attempts.pop(identifier, None)

    def get_stats(self, identifier: str) -> dict:
        """Get current rate limit stats (non-async)."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=60)

        attempts = [
            ts for ts in self.attempts.get(identifier, [])
            if ts > window_start
        ]

        return {
            "count": len(attempts),
            "oldest": attempts[0].isoformat() if attempts else None,
            "newest": attempts[-1].isoformat() if attempts else None,
        }


# Global rate limiter instance
form_submission_limiter = RateLimiter()
api_rate_limiter = RateLimiter()
tracking_rate_limiter = RateLimiter()
