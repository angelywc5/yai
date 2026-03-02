"""管理后台 API 集成测试。

验证管理员权限控制和路由可达性。
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.core.models import User


def _make_admin_user(user_id: str = "admin_001") -> MagicMock:
    """创建 mock 管理员用户。"""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = "admin@example.com"
    user.username = "admin"
    user.display_name = "Admin"
    user.credits = 9999
    user.email_verified = True
    user.is_admin = True
    user.avatar_url = None
    user.can_create_character = True
    user.can_create_scene = True
    user.created_at = datetime.now(timezone.utc)
    return user


def _make_normal_user(user_id: str = "user_001") -> MagicMock:
    """创建 mock 普通用户。"""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = "user@example.com"
    user.username = "normaluser"
    user.display_name = "Normal User"
    user.credits = 500
    user.email_verified = True
    user.is_admin = False
    user.avatar_url = None
    user.can_create_character = True
    user.can_create_scene = True
    user.created_at = datetime.now(timezone.utc)
    return user


# ============================================================================
# Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def admin_client():
    """管理员角色的测试客户端。"""
    from main import app
    from src.api.deps import get_current_admin, get_current_user, get_db_session

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.refresh = AsyncMock()

    admin_user = _make_admin_user()

    async def override_db_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_current_admin] = lambda: admin_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, mock_session, admin_user

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def normal_client():
    """普通用户角色的测试客户端（验证 403 拒绝）。"""
    from main import app
    from src.api.deps import get_current_admin, get_current_user, get_db_session

    mock_session = AsyncMock()
    normal_user = _make_normal_user()

    async def override_db_session():
        yield mock_session

    from fastapi import HTTPException

    async def reject_admin():
        raise HTTPException(status_code=403, detail={"message": "需要管理员权限", "code": "AUTH_FORBIDDEN"})

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_current_user] = lambda: normal_user
    app.dependency_overrides[get_current_admin] = reject_admin

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ============================================================================
# 非管理员禁止访问测试
# ============================================================================


class TestNonAdminForbidden:
    """非管理员访问管理接口应被拒绝。"""

    @pytest.mark.asyncio
    async def test_non_admin_get_users(self, normal_client) -> None:
        """非管理员访问 /admin/users 返回 403。"""
        resp = await normal_client.get("/api/v1/admin/users")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_non_admin_adjust_credits(self, normal_client) -> None:
        """非管理员调整积分被拒绝。"""
        resp = await normal_client.put(
            "/api/v1/admin/users/user_001/credits",
            json={"user_id": "user_001", "amount": 100, "reason": "测试"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_non_admin_get_models(self, normal_client) -> None:
        """非管理员获取模型状态被拒绝。"""
        resp = await normal_client.get("/api/v1/admin/models")
        assert resp.status_code == 403


# ============================================================================
# 管理员用户管理测试
# ============================================================================


class TestAdminUserManagement:
    """管理员用户管理测试。"""

    @pytest.mark.asyncio
    async def test_list_users_route_accessible(self, admin_client) -> None:
        """管理员可以访问用户列表接口。"""
        client, session, _ = admin_client

        with patch(
            "src.api.admin_routes._admin_svc.list_users",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "size": 20,
                "pages": 0,
            }
            resp = await client.get("/api/v1/admin/users")
            assert resp.status_code == 200
            data = resp.json()
            assert "items" in data

    @pytest.mark.asyncio
    async def test_get_user_detail_route(self, admin_client) -> None:
        """管理员获取用户详情。"""
        client, session, _ = admin_client

        with patch(
            "src.api.admin_routes._admin_svc.get_user_detail",
            new_callable=AsyncMock,
        ) as mock_detail:
            mock_detail.return_value = {
                "id": "user_001",
                "email": "user@example.com",
                "username": "testuser",
                "display_name": "Test",
                "email_verified": True,
                "credits": 500,
                "is_admin": False,
                "can_create_character": True,
                "can_create_scene": True,
                "avatar_url": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "character_count": 0,
                "scene_count": 0,
            }
            resp = await client.get("/api/v1/admin/users/user_001")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_adjust_credits_success(self, admin_client) -> None:
        """管理员调整用户积分成功。"""
        client, session, admin_user = admin_client

        with patch(
            "src.api.admin_routes._admin_svc.adjust_credits",
            new_callable=AsyncMock,
        ) as mock_adjust:
            mock_adjust.return_value = None
            resp = await client.put(
                "/api/v1/admin/users/user_001/credits",
                json={"user_id": "user_001", "amount": 100, "reason": "管理员充值"},
            )
            assert resp.status_code == 200
            assert "积分调整成功" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_update_permissions_success(self, admin_client) -> None:
        """更新用户权限成功。"""
        client, session, _ = admin_client

        with patch(
            "src.api.admin_routes._admin_svc.update_user_permissions",
            new_callable=AsyncMock,
        ) as mock_update:
            mock_update.return_value = {
                "message": "权限更新成功",
                "can_create_character": False,
                "can_create_scene": True,
            }
            resp = await client.put(
                "/api/v1/admin/users/user_001/permissions",
                json={
                    "can_create_character": False,
                    "can_create_scene": True,
                },
            )
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_user_consumption_7d(self, admin_client) -> None:
        """获取用户近 7 天消耗。"""
        client, session, _ = admin_client

        with patch(
            "src.api.admin_routes._admin_svc.get_user_recent_consumption",
            new_callable=AsyncMock,
        ) as mock_consumption:
            mock_consumption.return_value = {
                "user_id": "user_001",
                "window_days": 7,
                "total_consumed": 100,
                "total_refunded": 10,
                "net_consumed": 90,
                "daily": [],
                "recent_transactions": [],
            }
            resp = await client.get(
                "/api/v1/admin/users/user_001/consumption?days=7"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["window_days"] == 7

    @pytest.mark.asyncio
    async def test_get_user_consumption_30d(self, admin_client) -> None:
        """获取用户近 30 天消耗。"""
        client, session, _ = admin_client

        with patch(
            "src.api.admin_routes._admin_svc.get_user_recent_consumption",
            new_callable=AsyncMock,
        ) as mock_consumption:
            mock_consumption.return_value = {
                "user_id": "user_001",
                "window_days": 30,
                "total_consumed": 500,
                "total_refunded": 50,
                "net_consumed": 450,
                "daily": [],
                "recent_transactions": [],
            }
            resp = await client.get(
                "/api/v1/admin/users/user_001/consumption?days=30"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["window_days"] == 30


# ============================================================================
# 管理员资源管理测试
# ============================================================================


class TestAdminResourceManagement:
    """管理员资源管理测试。"""

    @pytest.mark.asyncio
    async def test_list_user_characters(self, admin_client) -> None:
        """获取用户角色卡列表。"""
        client, session, _ = admin_client

        with patch(
            "src.api.admin_routes._resource_svc.list_user_characters",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "size": 20,
                "pages": 0,
            }
            resp = await client.get("/api/v1/admin/users/user_001/characters")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_user_character(self, admin_client) -> None:
        """删除用户角色卡（软删除）。"""
        client, session, _ = admin_client

        with patch(
            "src.api.admin_routes._resource_svc.admin_delete_user_character",
            new_callable=AsyncMock,
        ) as mock_del:
            mock_del.return_value = None
            resp = await client.delete(
                "/api/v1/admin/users/user_001/characters/char_001"
            )
            assert resp.status_code == 200
            assert "角色已删除" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_list_user_scenes(self, admin_client) -> None:
        """获取用户场景卡列表。"""
        client, session, _ = admin_client

        with patch(
            "src.api.admin_routes._resource_svc.list_user_scenes",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "size": 20,
                "pages": 0,
            }
            resp = await client.get("/api/v1/admin/users/user_001/scenes")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_user_scene(self, admin_client) -> None:
        """删除用户场景卡（软删除）。"""
        client, session, _ = admin_client

        with patch(
            "src.api.admin_routes._resource_svc.admin_delete_user_scene",
            new_callable=AsyncMock,
        ) as mock_del:
            mock_del.return_value = None
            resp = await client.delete(
                "/api/v1/admin/users/user_001/scenes/scene_001"
            )
            assert resp.status_code == 200
            assert "场景已删除" in resp.json()["message"]


# ============================================================================
# 模型管理测试
# ============================================================================


class TestAdminModelManagement:
    """管理员模型管理测试。"""

    @pytest.mark.asyncio
    async def test_get_model_status(self, admin_client) -> None:
        """获取模型开关状态。"""
        client, session, _ = admin_client

        with patch(
            "src.api.admin_routes._resource_svc.get_model_status",
            new_callable=AsyncMock,
        ) as mock_status:
            mock_status.return_value = {
                "speed": True,
                "pro": True,
                "elite": False,
            }
            resp = await client.get("/api/v1/admin/models")
            assert resp.status_code == 200
            data = resp.json()
            assert data["speed"] is True
            assert data["elite"] is False

    @pytest.mark.asyncio
    async def test_toggle_model(self, admin_client) -> None:
        """切换模型启用状态。"""
        client, session, _ = admin_client

        with patch(
            "src.api.admin_routes._resource_svc.toggle_model",
            new_callable=AsyncMock,
        ) as mock_toggle:
            mock_toggle.return_value = None
            resp = await client.put(
                "/api/v1/admin/models/speed/toggle",
                json={"enabled": False},
            )
            assert resp.status_code == 200
            assert "已禁用" in resp.json()["message"]
