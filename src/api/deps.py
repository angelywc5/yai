"""FastAPI 依赖注入。"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.core.exceptions import ForbiddenError, UnauthorizedError
from src.core.models import User
from src.repositories.token_repo import VerificationTokenRepository
from src.repositories.user_repo import UserRepository
from src.services.auth_service import AuthService
from src.services.email_service import EmailService
from src.utils.database import db_engine
from src.utils.security import JwtTokenManager, PasswordHasher

# ============================================================================
# 数据库会话
# ============================================================================


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话。"""
    async with db_engine.get_session() as session:
        yield session


# ============================================================================
# 安全工具
# ============================================================================


def get_password_hasher() -> PasswordHasher:
    """获取密码哈希器。"""
    return PasswordHasher()


def get_jwt_manager() -> JwtTokenManager:
    """获取 JWT 管理器。"""
    settings = get_settings()
    return JwtTokenManager(
        secret_key=settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


# ============================================================================
# Repositories
# ============================================================================


def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    """获取用户仓储。"""
    return UserRepository(session)


def get_token_repo(
    session: AsyncSession = Depends(get_db_session),
) -> VerificationTokenRepository:
    """获取令牌仓储。"""
    return VerificationTokenRepository(session)


# ============================================================================
# Services
# ============================================================================


def get_email_service() -> EmailService:
    """获取邮件服务。"""
    settings = get_settings()
    return EmailService(settings)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    token_repo: VerificationTokenRepository = Depends(get_token_repo),
    email_service: EmailService = Depends(get_email_service),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    jwt_manager: JwtTokenManager = Depends(get_jwt_manager),
) -> AuthService:
    """获取认证服务。"""
    settings = get_settings()
    return AuthService(
        user_repo, token_repo, email_service, password_hasher, jwt_manager, settings
    )


# ============================================================================
# 认证依赖
# ============================================================================


async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    从 HttpOnly Cookie 中获取当前用户。

    Raises:
        UnauthorizedError: 未登录或 Token 无效
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise UnauthorizedError("未登录")

    return await auth_service.get_current_user(access_token)


async def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """
    校验管理员权限。

    Raises:
        ForbiddenError: 权限不足
    """
    if not user.is_admin:
        raise ForbiddenError("需要管理员权限")

    return user
