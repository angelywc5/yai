"""安全工具：密码哈希、JWT 管理、Cookie 设置。"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Response
from jose import JWTError, jwt

from src.core.exceptions import TokenExpiredError, TokenInvalidError

logger = logging.getLogger(__name__)


class PasswordHasher:
    """密码哈希工具（bcrypt）。"""

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码（自动加盐）。"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码。"""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception as e:
            logger.warning(f"密码验证失败: {e}")
            return False


class JwtTokenManager:
    """JWT 令牌管理。"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, user_id: str, expires_minutes: int) -> str:
        """创建 Access Token。"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        payload = {
            "sub": user_id,
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str, expires_minutes: int) -> str:
        """创建 Refresh Token。"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str, token_type: str | None = None) -> dict:
        """
        解析 JWT Token。

        Args:
            token: JWT Token 字符串
            token_type: 期望的 token 类型 ("access" | "refresh")，None 表示不校验类型

        Raises:
            TokenExpiredError: Token 已过期
            TokenInvalidError: Token 无效或类型不匹配
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 校验 token 类型
            if token_type and payload.get("type") != token_type:
                raise TokenInvalidError()

            return payload
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError() from e
        except JWTError as e:
            raise TokenInvalidError() from e


class CookieHelper:
    """Cookie 设置辅助工具。"""

    @staticmethod
    def set_auth_cookies(
        response: Response,
        access_token: str,
        refresh_token: str,
        secure: bool = True,
    ) -> None:
        """设置认证 Cookie（HttpOnly + SameSite）。"""
        # Access Token Cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=secure,
            samesite="lax",
            max_age=7 * 24 * 3600,  # 7 天
            path="/",
        )

        # Refresh Token Cookie（路径限制）
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=secure,
            samesite="lax",
            max_age=14 * 24 * 3600,  # 14 天
            path="/api/v1/auth/refresh",
        )

    @staticmethod
    def clear_auth_cookies(response: Response) -> None:
        """清除认证 Cookie。"""
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")
