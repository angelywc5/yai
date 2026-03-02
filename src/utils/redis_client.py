"""Redis 连接池管理。"""

from __future__ import annotations

import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisClientManager:
    """Redis 连接池管理器。"""

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    async def initialize(
        self,
        redis_url: str,
        max_connections: int = 20,
    ) -> None:
        """创建 aioredis 连接池。"""
        self._client = aioredis.from_url(
            redis_url,
            max_connections=max_connections,
            decode_responses=True,
        )
        await self._client.ping()
        logger.info("Redis connected (max_connections=%d)", max_connections)

    async def shutdown(self) -> None:
        """关闭连接池。"""
        if self._client is not None:
            await self._client.aclose()
            logger.info("Redis connection closed")

    @property
    def client(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("Redis client not initialized")
        return self._client


redis_manager = RedisClientManager()
