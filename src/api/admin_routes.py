"""管理后台 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_admin, get_db_session
from src.core.models import User
from src.core.schemas import (
    AdminCreditAdjustRequest,
    AdminUserConsumptionResponse,
    AdminUserPermissionRequest,
    CharacterResponse,
    MessageResponse,
    ModelStatusResponse,
    ModelTier,
    ModelToggleRequest,
    PaginatedResponse,
    SceneResponse,
    UserDetailResponse,
    UserResponse,
)
from src.services.admin_service import AdminService
from src.services.admin_resource_service import AdminResourceService

router = APIRouter()

_admin_svc = AdminService()
_resource_svc = AdminResourceService()


# ============================================================================
# 用户管理
# ============================================================================


@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    search: str | None = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(get_current_admin),
):
    """用户列表（分页 + 搜索）。"""
    return await _admin_svc.list_users(session, search=search, page=page, size=size)


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str = Path(...),
    session: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(get_current_admin),
):
    """用户详情。"""
    return await _admin_svc.get_user_detail(session, user_id)


@router.put("/users/{user_id}/credits")
async def adjust_credits(
    user_id: str = Path(...),
    body: AdminCreditAdjustRequest = ...,
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_current_admin),
):
    """管理员积分调整。"""
    await _admin_svc.adjust_credits(
        session, user_id, body.amount, body.reason, admin.id
    )
    await session.commit()
    return {"message": "积分调整成功"}


@router.put("/users/{user_id}/permissions")
async def update_permissions(
    user_id: str = Path(...),
    body: AdminUserPermissionRequest = ...,
    session: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(get_current_admin),
):
    """更新用户权限。"""
    result = await _admin_svc.update_user_permissions(
        session, user_id, body.can_create_character, body.can_create_scene
    )
    await session.commit()
    return result


@router.get(
    "/users/{user_id}/consumption",
    response_model=AdminUserConsumptionResponse,
)
async def get_user_consumption(
    user_id: str = Path(...),
    days: int = Query(7, ge=1, le=90),
    session: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(get_current_admin),
):
    """用户近期积分消耗（7/30 天）。"""
    return await _admin_svc.get_user_recent_consumption(session, user_id, days)


# ============================================================================
# 用户资源管理
# ============================================================================


@router.get(
    "/users/{user_id}/characters",
    response_model=PaginatedResponse[CharacterResponse],
)
async def list_user_characters(
    user_id: str = Path(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(get_current_admin),
):
    """用户角色卡列表。"""
    return await _resource_svc.list_user_characters(
        session, user_id, page=page, size=size
    )


@router.delete("/users/{user_id}/characters/{character_id}")
async def delete_user_character(
    user_id: str = Path(...),
    character_id: str = Path(...),
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_current_admin),
):
    """删除用户角色卡。"""
    await _resource_svc.admin_delete_user_character(
        session, user_id, character_id, admin.id
    )
    await session.commit()
    return {"message": "角色已删除"}


@router.get(
    "/users/{user_id}/scenes",
    response_model=PaginatedResponse[SceneResponse],
)
async def list_user_scenes(
    user_id: str = Path(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(get_current_admin),
):
    """用户场景卡列表。"""
    return await _resource_svc.list_user_scenes(
        session, user_id, page=page, size=size
    )


@router.delete("/users/{user_id}/scenes/{scene_id}")
async def delete_user_scene(
    user_id: str = Path(...),
    scene_id: str = Path(...),
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_current_admin),
):
    """删除用户场景卡。"""
    await _resource_svc.admin_delete_user_scene(
        session, user_id, scene_id, admin.id
    )
    await session.commit()
    return {"message": "场景已删除"}


@router.get(
    "/users/{user_id}/logs",
    response_model=PaginatedResponse[MessageResponse],
)
async def get_user_logs(
    user_id: str = Path(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(get_current_admin),
):
    """用户对话日志。"""
    return await _resource_svc.get_user_chat_logs(
        session, user_id, page=page, size=size
    )


# ============================================================================
# 角色管理
# ============================================================================


@router.get("/characters", response_model=PaginatedResponse[CharacterResponse])
async def list_characters(
    search: str | None = Query(None),
    creator_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(get_current_admin),
):
    """角色列表（管理员视角）。"""
    return await _resource_svc.list_characters(
        session, search=search, creator_id=creator_id, page=page, size=size
    )


@router.get("/characters/{character_id}", response_model=CharacterResponse)
async def get_character_detail(
    character_id: str = Path(...),
    session: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(get_current_admin),
):
    """角色详情（管理员视角，含完整 definition）。"""
    from sqlalchemy import select as sa_select, and_
    from src.core.models import Character as CharModel, User as UserModel

    row = (
        await session.execute(
            sa_select(CharModel, UserModel)
            .join(UserModel, CharModel.creator_id == UserModel.id)
            .where(
                and_(CharModel.id == character_id, CharModel.is_deleted.is_(False))
            )
        )
    ).one_or_none()
    if not row:
        from src.core.exceptions import ResourceNotFoundError

        raise ResourceNotFoundError("Character", character_id)
    c, u = row
    from src.services.admin_resource_service import _build_character_response

    return _build_character_response(c, u)


@router.delete("/characters/{character_id}")
async def delete_character(
    character_id: str = Path(...),
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_current_admin),
):
    """管理员删除角色。"""
    await _resource_svc.admin_delete_character(session, character_id, admin.id)
    await session.commit()
    return {"message": "角色已删除"}


# ============================================================================
# 场景管理
# ============================================================================


@router.get("/scenes", response_model=PaginatedResponse[SceneResponse])
async def list_scenes(
    search: str | None = Query(None),
    creator_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(get_current_admin),
):
    """场景列表（管理员视角）。"""
    return await _resource_svc.list_scenes(
        session, search=search, creator_id=creator_id, page=page, size=size
    )


@router.get("/scenes/{scene_id}", response_model=SceneResponse)
async def get_scene_detail(
    scene_id: str = Path(...),
    session: AsyncSession = Depends(get_db_session),
    _admin: User = Depends(get_current_admin),
):
    """场景详情（管理员视角）。"""
    from sqlalchemy import select as sa_select, and_
    from src.core.models import Scene as ScModel, User as UserModel

    row = (
        await session.execute(
            sa_select(ScModel, UserModel)
            .join(UserModel, ScModel.creator_id == UserModel.id)
            .where(and_(ScModel.id == scene_id, ScModel.is_deleted.is_(False)))
        )
    ).one_or_none()
    if not row:
        from src.core.exceptions import ResourceNotFoundError

        raise ResourceNotFoundError("Scene", scene_id)
    s, u = row
    from src.services.admin_resource_service import _build_scene_response

    return _build_scene_response(s, u)


@router.delete("/scenes/{scene_id}")
async def delete_scene(
    scene_id: str = Path(...),
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_current_admin),
):
    """管理员删除场景。"""
    await _resource_svc.admin_delete_scene(session, scene_id, admin.id)
    await session.commit()
    return {"message": "场景已删除"}


# ============================================================================
# 模型管理
# ============================================================================


@router.get("/models", response_model=ModelStatusResponse)
async def get_model_status(
    _admin: User = Depends(get_current_admin),
):
    """获取模型开关状态。"""
    status = await _resource_svc.get_model_status()
    return ModelStatusResponse(**status)


@router.put("/models/{tier}/toggle")
async def toggle_model(
    tier: ModelTier = Path(...),
    body: ModelToggleRequest = ...,
    _admin: User = Depends(get_current_admin),
):
    """切换模型启用状态。"""
    await _resource_svc.toggle_model(tier, body.enabled)
    return {"message": f"模型 {tier.value} {'已启用' if body.enabled else '已禁用'}"}
