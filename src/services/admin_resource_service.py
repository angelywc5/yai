"""管理后台业务服务 — 资源管理 + 模型开关。"""

from __future__ import annotations

import logging
import math

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Character, Message, Scene, SceneCharacter, User
from src.core.schemas import (
    CharacterResponse,
    MessageResponse,
    ModelTier,
    PaginatedResponse,
    SceneResponse,
)
from src.core.exceptions import ResourceNotFoundError
from src.utils.redis_client import redis_manager

logger = logging.getLogger(__name__)

MODEL_SWITCHES_KEY = "yai:model_switches"


class AdminResourceService:
    """
    管理后台资源管理服务。

    职责：角色/场景列表与删除、用户资源管理、对话日志、模型开关。
    """

    # ------------------------------------------------------------------
    # 用户资源管理
    # ------------------------------------------------------------------

    async def list_user_characters(
        self,
        session: AsyncSession,
        user_id: str,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[CharacterResponse]:
        """列出某用户创建的角色卡。"""
        conditions = [
            Character.creator_id == user_id,
            Character.is_deleted.is_(False),
        ]
        total = (
            await session.execute(
                select(func.count()).select_from(Character).where(and_(*conditions))
            )
        ).scalar() or 0

        offset = (page - 1) * size
        rows = (
            await session.execute(
                select(Character, User)
                .join(User, Character.creator_id == User.id)
                .where(and_(*conditions))
                .order_by(desc(Character.created_at))
                .offset(offset)
                .limit(size)
            )
        ).all()

        items = [
            _build_character_response(c, u) for c, u in rows
        ]
        pages = max(1, math.ceil(total / size))
        return PaginatedResponse[CharacterResponse](
            items=items, total=total, page=page, size=size, pages=pages
        )

    async def admin_delete_user_character(
        self,
        session: AsyncSession,
        user_id: str,
        character_id: str,
        operator_id: str,
    ) -> None:
        """删除用户角色卡（软删除）。"""
        character = (
            await session.execute(
                select(Character).where(
                    and_(
                        Character.id == character_id,
                        Character.creator_id == user_id,
                        Character.is_deleted.is_(False),
                    )
                )
            )
        ).scalar_one_or_none()
        if not character:
            raise ResourceNotFoundError("Character", character_id)

        await _soft_delete_character(session, character)
        logger.info(
            "Admin delete user character: char=%s user=%s operator=%s",
            character_id, user_id, operator_id,
        )

    async def list_user_scenes(
        self,
        session: AsyncSession,
        user_id: str,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[SceneResponse]:
        """列出某用户创建的场景卡。"""
        conditions = [Scene.creator_id == user_id, Scene.is_deleted.is_(False)]
        total = (
            await session.execute(
                select(func.count()).select_from(Scene).where(and_(*conditions))
            )
        ).scalar() or 0

        offset = (page - 1) * size
        rows = (
            await session.execute(
                select(Scene, User)
                .join(User, Scene.creator_id == User.id)
                .where(and_(*conditions))
                .order_by(desc(Scene.created_at))
                .offset(offset)
                .limit(size)
            )
        ).all()

        items = [_build_scene_response(s, u) for s, u in rows]
        pages = max(1, math.ceil(total / size))
        return PaginatedResponse[SceneResponse](
            items=items, total=total, page=page, size=size, pages=pages
        )

    async def admin_delete_user_scene(
        self,
        session: AsyncSession,
        user_id: str,
        scene_id: str,
        operator_id: str,
    ) -> None:
        """删除用户场景卡（软删除）。"""
        scene = (
            await session.execute(
                select(Scene).where(
                    and_(
                        Scene.id == scene_id,
                        Scene.creator_id == user_id,
                        Scene.is_deleted.is_(False),
                    )
                )
            )
        ).scalar_one_or_none()
        if not scene:
            raise ResourceNotFoundError("Scene", scene_id)

        await _soft_delete_scene(session, scene)
        logger.info(
            "Admin delete user scene: scene=%s user=%s operator=%s",
            scene_id, user_id, operator_id,
        )

    # ------------------------------------------------------------------
    # 角色管理（全局）
    # ------------------------------------------------------------------

    async def list_characters(
        self,
        session: AsyncSession,
        search: str | None = None,
        creator_id: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[CharacterResponse]:
        """搜索/分页所有角色（管理员可见包括私有）。"""
        conditions = [Character.is_deleted.is_(False)]
        if search:
            conditions.append(Character.name.ilike(f"%{search}%"))
        if creator_id:
            conditions.append(Character.creator_id == creator_id)

        total = (
            await session.execute(
                select(func.count()).select_from(Character).where(and_(*conditions))
            )
        ).scalar() or 0

        offset = (page - 1) * size
        rows = (
            await session.execute(
                select(Character, User)
                .join(User, Character.creator_id == User.id)
                .where(and_(*conditions))
                .order_by(desc(Character.created_at))
                .offset(offset)
                .limit(size)
            )
        ).all()

        items = [_build_character_response(c, u) for c, u in rows]
        pages = max(1, math.ceil(total / size))
        return PaginatedResponse[CharacterResponse](
            items=items, total=total, page=page, size=size, pages=pages
        )

    async def admin_delete_character(
        self, session: AsyncSession, character_id: str, operator_id: str
    ) -> None:
        """管理员删除角色（软删除 + 清除关联）。"""
        character = (
            await session.execute(
                select(Character).where(
                    and_(Character.id == character_id, Character.is_deleted.is_(False))
                )
            )
        ).scalar_one_or_none()
        if not character:
            raise ResourceNotFoundError("Character", character_id)

        await _soft_delete_character(session, character)
        logger.info(
            "Admin delete character: id=%s operator=%s", character_id, operator_id
        )

    # ------------------------------------------------------------------
    # 场景管理（全局）
    # ------------------------------------------------------------------

    async def list_scenes(
        self,
        session: AsyncSession,
        search: str | None = None,
        creator_id: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[SceneResponse]:
        """搜索/分页所有场景。"""
        conditions = [Scene.is_deleted.is_(False)]
        if search:
            conditions.append(Scene.name.ilike(f"%{search}%"))
        if creator_id:
            conditions.append(Scene.creator_id == creator_id)

        total = (
            await session.execute(
                select(func.count()).select_from(Scene).where(and_(*conditions))
            )
        ).scalar() or 0

        offset = (page - 1) * size
        rows = (
            await session.execute(
                select(Scene, User)
                .join(User, Scene.creator_id == User.id)
                .where(and_(*conditions))
                .order_by(desc(Scene.created_at))
                .offset(offset)
                .limit(size)
            )
        ).all()

        items = [_build_scene_response(s, u) for s, u in rows]
        pages = max(1, math.ceil(total / size))
        return PaginatedResponse[SceneResponse](
            items=items, total=total, page=page, size=size, pages=pages
        )

    async def admin_delete_scene(
        self, session: AsyncSession, scene_id: str, operator_id: str
    ) -> None:
        """管理员删除场景（软删除 + 清除关联）。"""
        scene = (
            await session.execute(
                select(Scene).where(
                    and_(Scene.id == scene_id, Scene.is_deleted.is_(False))
                )
            )
        ).scalar_one_or_none()
        if not scene:
            raise ResourceNotFoundError("Scene", scene_id)

        await _soft_delete_scene(session, scene)
        logger.info("Admin delete scene: id=%s operator=%s", scene_id, operator_id)

    # ------------------------------------------------------------------
    # 对话日志
    # ------------------------------------------------------------------

    async def get_user_chat_logs(
        self,
        session: AsyncSession,
        user_id: str,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[MessageResponse]:
        """查看用户对话日志。"""
        conditions = [Message.user_id == user_id, Message.is_deleted.is_(False)]
        total = (
            await session.execute(
                select(func.count()).select_from(Message).where(and_(*conditions))
            )
        ).scalar() or 0

        offset = (page - 1) * size
        messages = (
            await session.execute(
                select(Message)
                .where(and_(*conditions))
                .order_by(desc(Message.created_at))
                .offset(offset)
                .limit(size)
            )
        ).scalars().all()

        items = [
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                token_count=m.token_count,
                turn_number=m.turn_number,
                feedback=m.feedback,
                is_pinned=m.is_pinned,
                created_at=m.created_at,
            )
            for m in messages
        ]
        pages = max(1, math.ceil(total / size))
        return PaginatedResponse[MessageResponse](
            items=items, total=total, page=page, size=size, pages=pages
        )

    # ------------------------------------------------------------------
    # 模型开关
    # ------------------------------------------------------------------

    async def toggle_model(self, tier: ModelTier, enabled: bool) -> None:
        """全局启用/禁用模型档位。"""
        redis = redis_manager.client
        await redis.hset(MODEL_SWITCHES_KEY, tier.value, "1" if enabled else "0")
        logger.info("Model toggle: tier=%s enabled=%s", tier.value, enabled)

    async def get_model_status(self) -> dict[str, bool]:
        """获取所有模型档位的启用状态。"""
        redis = redis_manager.client
        result = await redis.hgetall(MODEL_SWITCHES_KEY)
        return {
            tier.value: result.get(tier.value, "1") == "1"
            for tier in ModelTier
        }


# ======================================================================
# 辅助函数
# ======================================================================


async def _soft_delete_character(session: AsyncSession, character: Character) -> None:
    """软删除角色：标记 + 清除 SceneCharacter 关联 + 设为非公开。"""
    await session.execute(
        select(SceneCharacter)
        .where(SceneCharacter.character_id == character.id)
    )
    # 删除关联
    from sqlalchemy import delete as sa_delete

    await session.execute(
        sa_delete(SceneCharacter).where(SceneCharacter.character_id == character.id)
    )
    character.is_deleted = True
    character.deleted_at = func.now()
    character.is_public = False
    await session.flush()


async def _soft_delete_scene(session: AsyncSession, scene: Scene) -> None:
    """软删除场景：标记 + 清除 SceneCharacter 关联 + 设为非公开。"""
    from sqlalchemy import delete as sa_delete

    await session.execute(
        sa_delete(SceneCharacter).where(SceneCharacter.scene_id == scene.id)
    )
    scene.is_deleted = True
    scene.deleted_at = func.now()
    scene.is_public = False
    await session.flush()


def _build_character_response(character: Character, user: User) -> CharacterResponse:
    """构建角色响应 DTO。"""
    return CharacterResponse(
        id=character.id,
        name=character.name,
        avatar_url=character.avatar_url,
        avatar_source=character.avatar_source,
        tagline=character.tagline,
        definition=character.definition,
        tags=character.tags,
        is_public=character.is_public,
        chat_count=character.chat_count,
        like_count=character.like_count,
        creator_id=character.creator_id,
        creator_username=user.username,
        creator_display_name=user.display_name,
        created_at=character.created_at,
    )


def _build_scene_response(scene: Scene, user: User) -> SceneResponse:
    """构建场景响应 DTO。"""
    return SceneResponse(
        id=scene.id,
        name=scene.name,
        description=scene.description,
        cover_image_url=scene.cover_image_url,
        cover_source=scene.cover_source,
        genre=scene.genre,
        time_period=scene.time_period,
        setting_location=scene.setting_location,
        mood=scene.mood,
        player_objective=scene.player_objective,
        greeting=scene.greeting,
        allow_character_selection=scene.allow_character_selection,
        tags=scene.tags,
        is_public=scene.is_public,
        play_count=scene.play_count,
        creator_id=scene.creator_id,
        creator_username=user.username,
        creator_display_name=user.display_name,
        characters=[],
        created_at=scene.created_at,
    )
