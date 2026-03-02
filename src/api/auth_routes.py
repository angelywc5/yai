"""认证相关 API 路由。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import (
    get_auth_service,
    get_current_user,
    get_db_session,
)
from src.config.settings import get_settings
from src.core.exceptions import (
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    UnauthorizedError,
    UsernameAlreadyExistsError,
    YaiBaseError,
)
from src.core.models import User
from src.core.schemas import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from src.services.auth_service import AuthService
from src.utils.security import CookieHelper

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# 异常处理映射
# ============================================================================


def map_exception_to_http(error: YaiBaseError) -> HTTPException:
    """将业务异常映射为 HTTP 异常。"""
    status_code_map = {
        EmailAlreadyExistsError: 409,
        UsernameAlreadyExistsError: 409,
        InvalidCredentialsError: 401,
        EmailNotVerifiedError: 403,
        TokenExpiredError: 400,
        TokenInvalidError: 400,
        UnauthorizedError: 401,
    }

    status_code = status_code_map.get(type(error), 500)
    return HTTPException(
        status_code=status_code,
        detail={"message": error.message, "code": error.code},
    )


# ============================================================================
# 路由
# ============================================================================


@router.post("/register", status_code=201)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """
    用户注册。

    - 校验邮箱和用户名唯一性
    - 创建未验证用户
    - 发送验证邮件
    """
    try:
        await auth_service.register(
            email=request.email,
            password=request.password,
            username=request.username,
            display_name=request.display_name,
        )
        await session.commit()
        return {"message": "注册成功，请查收验证邮件"}
    except YaiBaseError as e:
        await session.rollback()
        raise map_exception_to_http(e) from e


@router.get("/verify/{token}")
async def verify_email(
    token: str,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """
    邮箱验证。

    - 验证 token
    - 激活用户并发放默认积分
    - 自动登录（设置 Cookie）
    """
    try:
        user = await auth_service.verify_email(token)
        await session.commit()

        # 生成登录 Token（跳过密码验证）
        settings = get_settings()
        access_token = auth_service.jwt_manager.create_access_token(
            user.id, settings.access_token_expire_minutes
        )
        refresh_token = auth_service.jwt_manager.create_refresh_token(
            user.id, settings.refresh_token_expire_minutes
        )

        CookieHelper.set_auth_cookies(
            response,
            access_token,
            refresh_token,
            secure=settings.environment == "production",
        )

        return {"message": "邮箱验证成功，已自动登录"}
    except YaiBaseError as e:
        await session.rollback()
        raise map_exception_to_http(e) from e


@router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """
    用户登录。

    - 验证邮箱和密码
    - 设置 HttpOnly Cookie
    """
    try:
        access_token, refresh_token = await auth_service.login(
            request.email, request.password
        )

        settings = get_settings()
        CookieHelper.set_auth_cookies(
            response,
            access_token,
            refresh_token,
            secure=settings.environment == "production",
        )

        return {"message": "登录成功"}
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e


@router.post("/logout")
async def logout(
    response: Response,
    _user: User = Depends(get_current_user),
) -> dict[str, str]:
    """登出（清除 Cookie）。"""
    CookieHelper.clear_auth_cookies(response)
    return {"message": "登出成功"}


@router.post("/refresh")
async def refresh_token(
    request: Response,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """
    刷新 Access Token。

    - 从 Cookie 读取 refresh_token
    - 生成新的 access_token
    """
    refresh_token_str = request.cookies.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(
            401, detail={"message": "未登录", "code": "AUTH_UNAUTHORIZED"}
        )

    try:
        new_access_token = await auth_service.refresh_token(refresh_token_str)

        settings = get_settings()
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=settings.environment == "production",
            samesite="lax",
            max_age=7 * 24 * 3600,
            path="/",
        )

        return {"message": "Token 刷新成功"}
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(get_current_user),
) -> UserResponse:
    """获取当前用户信息。"""
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        credits=user.credits,
        is_admin=user.is_admin,
        email_verified=user.email_verified,
        created_at=user.created_at,
    )
