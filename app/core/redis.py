"""
Redis client lifecycle and session management.
"""

from __future__ import annotations

import logging

from redis.asyncio import Redis, from_url

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Manages the lifecycle of the Redis async client.

    Usage (in events.py)::

        RedisManager.init(settings.redis_url)
        ...
        await RedisManager.close()
    """

    _client: Redis | None = None

    @classmethod
    def init(cls, redis_url: str) -> None:
        """
        Initialise the Redis async client.

        Args:
            redis_url: The connection URL for Redis.
        """
        if cls._client is not None:
            logger.warning("RedisManager.init() called more than once — skipping.")
            return

        cls._client = from_url(redis_url, decode_responses=True)
        logger.debug("Redis async client created")

    @classmethod
    async def close(cls) -> None:
        """Close the Redis connection pool."""
        if cls._client is None:
            return

        await cls._client.aclose()
        cls._client = None
        logger.debug("Redis async client closed")

    @classmethod
    def get_client(cls) -> Redis:
        """
        Get the active Redis client.

        Returns:
            The initialised Redis client.

        Raises:
            RuntimeError: If the RedisManager is not yet initialised.
        """
        if cls._client is None:
            raise RuntimeError("RedisManager is not initialised. Call init() first.")
        return cls._client
