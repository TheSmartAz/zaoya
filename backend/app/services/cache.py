"""Redis caching layer for published pages and analytics.

This module provides optional Redis caching for performance optimization.
Redis is optional - if not configured, caches will be in-memory or bypassed.
"""

import json
import logging
from typing import Optional, Any
from datetime import timedelta

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

from app.config import settings

logger = logging.getLogger(__name__)


class CacheBackend:
    """Abstract cache backend."""

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        raise NotImplementedError

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set a value in cache."""
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        raise NotImplementedError

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching a pattern. Returns count of deleted keys."""
        raise NotImplementedError

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        raise NotImplementedError

    async def close(self) -> None:
        """Close the connection."""
        pass


class RedisCache(CacheBackend):
    """Redis cache backend."""

    def __init__(self, url: str, **kwargs):
        if not REDIS_AVAILABLE:
            raise ImportError("redis-py is required for Redis caching")

        self.url = url
        self.kwargs = kwargs
        self._client: Optional[aioredis.Redis] = None

    async def _get_client(self) -> aioredis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = await aioredis.from_url(
                self.url,
                decode_responses=True,
                **self.kwargs
            )
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis."""
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set a value in Redis."""
        try:
            client = await self._get_client()
            serialized = json.dumps(value)
            if ttl:
                await client.setex(key, ttl, serialized)
            else:
                await client.set(key, serialized)
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")

    async def delete(self, key: str) -> None:
        """Delete a key from Redis."""
        try:
            client = await self._get_client()
            await client.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching a pattern."""
        try:
            client = await self._get_client()
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis delete_pattern failed: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            client = await self._get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Redis exists failed: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


class InMemoryCache(CacheBackend):
    """Fallback in-memory cache for development."""

    def __init__(self):
        self._cache: dict[str, tuple[Any, Optional[float]]] = {}
        # Each entry: (value, expiry_timestamp)

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from in-memory cache."""
        import time
        entry = self._cache.get(key)
        if entry is None:
            return None

        value, expiry = entry
        if expiry is not None and time.time() > expiry:
            del self._cache[key]
            return None

        return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set a value in in-memory cache."""
        import time
        expiry = (time.time() + ttl) if ttl else None
        self._cache[key] = (value, expiry)

    async def delete(self, key: str) -> None:
        """Delete a key from in-memory cache."""
        self._cache.pop(key, None)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching a pattern."""
        import fnmatch
        to_delete = [k for k in self._cache if fnmatch.fnmatch(k, pattern)]
        for k in to_delete:
            del self._cache[k]
        return len(to_delete)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in in-memory cache."""
        return key in self._cache


class NoOpCache(CacheBackend):
    """No-op cache that does nothing (for when caching is disabled)."""

    async def get(self, key: str) -> Optional[Any]:
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass

    async def delete(self, key: str) -> None:
        pass

    async def delete_pattern(self, pattern: str) -> int:
        return 0

    async def exists(self, key: str) -> bool:
        return False


# Global cache instance
_cache: Optional[CacheBackend] = None


def get_cache() -> CacheBackend:
    """Get the active cache backend."""
    global _cache
    if _cache is None:
        _cache = _create_cache()
    return _cache


def _create_cache() -> CacheBackend:
    """Create cache backend based on configuration."""
    redis_url = getattr(settings, "redis_url", None)

    if redis_url and REDIS_AVAILABLE:
        try:
            return RedisCache(
                url=redis_url,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Redis: {e}, using in-memory cache")

    # Fall back to in-memory cache for development
    if getattr(settings, "environment", None) == "development":
        return InMemoryCache()

    # No caching in production without Redis
    return NoOpCache()


async def close_cache() -> None:
    """Close the cache connection."""
    global _cache
    if _cache:
        await _cache.close()
        _cache = None


# ============================================================
# Cache key helpers
# ============================================================

class CacheKeys:
    """Standardized cache key generators."""

    @staticmethod
    def published_project(public_id: str) -> str:
        return f"project:published:{public_id}"

    @staticmethod
    def published_page(public_id: str, page_slug: str) -> str:
        return f"page:published:{public_id}:{page_slug}"

    @staticmethod
    def analytics_daily(project_id: str, date: str) -> str:
        return f"analytics:daily:{project_id}:{date}"

    @staticmethod
    def experiment_variant(experiment_id: str, visitor_id: str) -> str:
        return f"experiment:variant:{experiment_id}:{visitor_id}"

    @staticmethod
    def experiment_results(experiment_id: str) -> str:
        return f"experiment:results:{experiment_id}"

    @staticmethod
    def user_credits(user_id: str) -> str:
        return f"user:credits:{user_id}"

    @staticmethod
    def subscription_status(user_id: str) -> str:
        return f"user:subscription:{user_id}"


# ============================================================
# Cache TTL constants (in seconds)
# ============================================================

class CacheTTL:
    """Standard cache TTL values."""

    # Published content - cache for 1 hour
    PUBLISHED_PROJECT = 3600
    PUBLISHED_PAGE = 3600

    # Analytics - cache for 5 minutes
    ANALYTICS_DAILY = 300
    ANALYTICS_REALTIME = 60

    # Experiments - cache for 30 minutes
    EXPERIMENT_VARIANT = 1800

    # User data - cache for 5 minutes
    USER_CREDITS = 300
    SUBSCRIPTION_STATUS = 300

    # Short-lived caches
    SHORT = 60
    MEDIUM = 300
    LONG = 3600
    DAY = 86400
