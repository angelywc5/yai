"""FastAPI 中间件：限流 + 请求日志。"""

from __future__ import annotations

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config.settings import get_settings
from src.utils.rate_limiter import SlidingWindowRateLimiter
from src.utils.security import JwtTokenManager

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    基于 Redis 滑动窗口的限流中间件。

    - 对话接口：按 user_id 限流
    - 认证接口：按 IP 限流
    - 管理接口：不限流
    - 其他接口：按 user_id/IP 限流
    """

    def __init__(self, app, rate_limiter: SlidingWindowRateLimiter) -> None:
        super().__init__(app)
        self._limiter = rate_limiter
        settings = get_settings()
        self._route_limits: dict[str, tuple[int, int]] = {
            "/api/v1/chat/": (
                settings.rate_limit_chat_max,
                settings.rate_limit_chat_window,
            ),
            "/api/v1/auth/": (
                settings.rate_limit_auth_max,
                settings.rate_limit_auth_window,
            ),
        }
        self._default_limit = (
            settings.rate_limit_default_max,
            settings.rate_limit_default_window,
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # 管理接口跳过限流
        if path.startswith("/api/v1/admin/"):
            return await call_next(request)

        # 健康检查和文档跳过限流
        if path in ("/health", "/", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        # 确定限流参数
        max_req, window = self._default_limit
        for prefix, (m, w) in self._route_limits.items():
            if path.startswith(prefix):
                max_req, window = m, w
                break

        # 提取限流 key
        key = self._extract_key(request, path)

        is_limited, remaining = await self._limiter.is_rate_limited(
            key, max_req, window
        )

        if is_limited:
            retry_after = await self._limiter.get_reset_time(key, window)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "请求过于频繁，请稍后再试",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(max_req),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(retry_after),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_req)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    @staticmethod
    def _extract_key(request: Request, path: str) -> str:
        """提取限流 key：认证接口用 IP，其他用 user_id 或 IP。"""
        # 认证接口按 IP 限流
        if path.startswith("/api/v1/auth/"):
            return f"ip:{_get_client_ip(request)}"

        # 尝试从 Cookie 提取 user_id
        access_token = request.cookies.get("access_token")
        if access_token:
            try:
                settings = get_settings()
                manager = JwtTokenManager(
                    secret_key=settings.jwt_secret_key,
                    algorithm=settings.jwt_algorithm,
                )
                payload = manager.decode_token(access_token)
                user_id = payload.get("sub")
                if user_id:
                    return f"user:{user_id}"
            except Exception:
                pass

        return f"ip:{_get_client_ip(request)}"


class RequestLogMiddleware(BaseHTTPMiddleware):
    """请求日志记录中间件。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "%s %s %d %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


def _get_client_ip(request: Request) -> str:
    """提取客户端 IP，优先读取代理头。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"
