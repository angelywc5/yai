"""Redis 滑动窗口限流器。"""

from __future__ import annotations

import logging
import time

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """
    基于 Redis Sorted Set 的滑动窗口限流器。

    使用 Pipeline 原子操作确保并发安全：
    1. ZREMRANGEBYSCORE — 清理过期记录
    2. ZCARD — 统计当前窗口请求数
    3. ZADD — 添加当前请求时间戳
    4. EXPIRE — 设置 key TTL
    """

    KEY_PREFIX = "yai:ratelimit:"

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """
        检查请求是否触发限流。

        Args:
            key: 限流标识（如 user_id 或 IP）
            max_requests: 窗口内最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            (is_limited, remaining) — 是否被限流 + 剩余可用次数
        """
        now = time.time()
        window_start = now - window_seconds
        redis_key = f"{self.KEY_PREFIX}{key}"

        pipe = self._redis.pipeline(transaction=True)
        pipe.zremrangebyscore(redis_key, "-inf", window_start)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {str(now): now})
        pipe.expire(redis_key, window_seconds)
        results = await pipe.execute()

        current_count = results[1]

        if current_count >= max_requests:
            # 超出限制，移除刚添加的记录
            await self._redis.zrem(redis_key, str(now))
            remaining = 0
            return True, remaining

        remaining = max(0, max_requests - current_count - 1)
        return False, remaining

    async def get_reset_time(self, key: str, window_seconds: int) -> int:
        """获取限流重置剩余秒数。"""
        redis_key = f"{self.KEY_PREFIX}{key}"
        oldest = await self._redis.zrange(redis_key, 0, 0, withscores=True)
        if not oldest:
            return 0
        oldest_time = float(oldest[0][1])
        reset_at = oldest_time + window_seconds
        return max(0, int(reset_at - time.time()))
