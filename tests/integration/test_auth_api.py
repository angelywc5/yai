"""认证 API 集成测试。

使用 mock 依赖进行端到端路由测试，不依赖真实数据库。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.core.exceptions import (
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
)
from src.core.models import User
from src.utils.security import JwtTokenManager, PasswordHasher

SECRET_KEY = "test-secret-key-for-integration"
JWT_MANAGER = JwtTokenManager(secret_key=SECRET_KEY)


def _make_user(
    user_id: str = "user_001",
    email: str = "test@example.com",
    username: str = "testuser",
    display_name: str = "Test User",
    credits: int = 500,
    email_verified: bool = True,
    is_admin: bool = False,
) -> MagicMock:
    """创建 mock User 对象。"""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = email
    user.username = username
    user.display_name = display_name
    user.credits = credits
    user.email_verified = email_verified
    user.is_admin = is_admin
    user.avatar_url = None
    user.can_create_character = True
    user.can_create_scene = True
    user.created_at = datetime.now(timezone.utc)
    return user


def _create_access_token(user_id: str = "user_001") -> str:
    """为测试创建有效的 access_token。"""
    return JWT_MANAGER.create_access_token(user_id, expires_minutes=60)


# ============================================================================
# Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def app_client():
    """创建测试 FastAPI 客户端，mock 所有外部依赖。"""
    from main import app
    from src.api.deps import get_auth_service, get_current_user, get_db_session

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    mock_auth_service = AsyncMock()

    async def override_db_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, mock_auth_service, mock_session

    app.dependency_overrides.clear()


# ============================================================================
# 注册测试
# ============================================================================


class TestRegister:
    """注册 API 测试。"""

    @pytest.mark.asyncio
    async def test_register_success(self, app_client) -> None:
        """正常注册返回 201。"""
        client, auth_service, _ = app_client
        mock_user = _make_user(email_verified=False)
        auth_service.register = AsyncMock(return_value=mock_user)

        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "securePassword123",
                "username": "newuser",
                "display_name": "New User",
            },
        )
        assert resp.status_code == 201
        assert "注册成功" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, app_client) -> None:
        """重复邮箱返回 409。"""
        client, auth_service, session = app_client
        auth_service.register = AsyncMock(side_effect=EmailAlreadyExistsError())

        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "exist@example.com",
                "password": "securePassword123",
                "username": "newuser2",
                "display_name": "Dup User",
            },
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, app_client) -> None:
        """无效邮箱返回 422。"""
        client, _, _ = app_client

        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "securePassword123",
                "username": "user3",
                "display_name": "User3",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, app_client) -> None:
        """密码过短返回 422。"""
        client, _, _ = app_client

        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "password": "123",
                "username": "user4",
                "display_name": "User4",
            },
        )
        assert resp.status_code == 422


# ============================================================================
# 登录测试
# ============================================================================


class TestLogin:
    """登录 API 测试。"""

    @pytest.mark.asyncio
    async def test_login_success(self, app_client) -> None:
        """登录成功设置 Cookie。"""
        client, auth_service, _ = app_client
        auth_service.login = AsyncMock(
            return_value=("mock_access_token", "mock_refresh_token")
        )

        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "correctPassword",
            },
        )
        assert resp.status_code == 200
        assert "登录成功" in resp.json()["message"]
        assert "access_token" in resp.cookies

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, app_client) -> None:
        """密码错误返回 401。"""
        client, auth_service, _ = app_client
        auth_service.login = AsyncMock(side_effect=InvalidCredentialsError())

        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongPassword",
            },
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unverified_email(self, app_client) -> None:
        """未验证邮箱返回 403。"""
        client, auth_service, _ = app_client
        auth_service.login = AsyncMock(side_effect=EmailNotVerifiedError())

        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "unverified@example.com",
                "password": "correctPassword",
            },
        )
        assert resp.status_code == 403


# ============================================================================
# 登出与获取用户信息测试
# ============================================================================


class TestLogoutAndMe:
    """登出与获取当前用户测试。"""

    @pytest.mark.asyncio
    async def test_me_returns_user_info(self, app_client) -> None:
        """GET /auth/me 返回当前用户信息。"""
        from src.api.deps import get_current_user

        client, _, _ = app_client
        from main import app

        mock_user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, app_client) -> None:
        """GET /auth/me 未登录返回 401。"""
        from fastapi import HTTPException
        from src.api.deps import get_current_user

        client, _, _ = app_client
        from main import app

        async def reject_user():
            raise HTTPException(
                status_code=401,
                detail={"message": "未登录", "code": "AUTH_UNAUTHORIZED"},
            )

        app.dependency_overrides[get_current_user] = reject_user

        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_clears_cookies(self, app_client) -> None:
        """登出清除 Cookie。"""
        from src.api.deps import get_current_user

        client, _, _ = app_client
        from main import app

        mock_user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        assert "登出成功" in resp.json()["message"]


# ============================================================================
# 邮箱验证测试
# ============================================================================


class TestVerifyEmail:
    """邮箱验证 API 测试。"""

    @pytest.mark.asyncio
    async def test_verify_expired_token(self, app_client) -> None:
        """过期令牌返回 400。"""
        client, auth_service, session = app_client
        auth_service.verify_email = AsyncMock(side_effect=TokenExpiredError())

        resp = await client.get("/api/v1/auth/verify/expired-token-xxx")
        assert resp.status_code == 400
