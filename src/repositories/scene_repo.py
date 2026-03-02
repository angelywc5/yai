"""场景数据访问层。"""

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.models import Scene, SceneCharacter, User
from src.utils.id_generator import new_id


class SceneRepository:
    """场景数据访问。"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        name: str,
        description: str,
        scene_definition: str,
        greeting: str,
        creator_id: str,
        cover_image_url: str | None,
        cover_source: str,
        allow_character_selection: bool,
        is_public: bool,
        genre: str = "",
        time_period: str = "",
        setting_location: str = "",
        mood: str = "",
        player_objective: str = "",
        tags: list[str] | None = None,
    ) -> Scene:
        """创建场景。"""
        scene = Scene(
            id=new_id(),
            name=name,
            description=description,
            scene_definition=scene_definition,
            greeting=greeting,
            creator_id=creator_id,
            cover_image_url=cover_image_url,
            cover_source=cover_source,
            allow_character_selection=allow_character_selection,
            is_public=is_public,
            genre=genre,
            time_period=time_period,
            setting_location=setting_location,
            mood=mood,
            player_objective=player_objective,
            tags=tags or [],
        )
        self._session.add(scene)
        await self._session.flush()
        await self._session.refresh(scene)
        return scene

    async def get_by_id(self, scene_id: str) -> Scene | None:
        """根据 ID 获取场景（不过滤软删除）。"""
        stmt = select(Scene).where(Scene.id == scene_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_active(self, scene_id: str) -> Scene | None:
        """根据 ID 获取场景（过滤软删除）。"""
        stmt = select(Scene).where(
            and_(Scene.id == scene_id, Scene.is_deleted.is_(False))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_characters(self, scene_id: str) -> Scene | None:
        """获取场景及关联角色。"""
        stmt = (
            select(Scene)
            .options(selectinload(Scene.scene_characters))
            .where(and_(Scene.id == scene_id, Scene.is_deleted.is_(False)))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_creator(
        self, creator_id: str, offset: int, limit: int
    ) -> list[Scene]:
        """获取创建者的所有场景（含软删除）。"""
        stmt = (
            select(Scene)
            .where(Scene.creator_id == creator_id)
            .order_by(desc(Scene.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_creator(self, creator_id: str) -> int:
        """统计创建者的场景总数（含软删除）。"""
        stmt = (
            select(func.count())
            .select_from(Scene)
            .where(Scene.creator_id == creator_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_public(
        self, offset: int, limit: int, sort: str = "popular"
    ) -> list[Scene]:
        """
        获取公开场景列表，支持排序：
        - popular: 按 play_count DESC
        - newest: 按 created_at DESC
        - most_chats: 按 play_count DESC
        """
        order_clause = (
            desc(Scene.created_at) if sort == "newest" else desc(Scene.play_count)
        )
        stmt = (
            select(Scene)
            .where(and_(Scene.is_public.is_(True), Scene.is_deleted.is_(False)))
            .order_by(order_clause, desc(Scene.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_public(self) -> int:
        """统计公开场景总数。"""
        stmt = (
            select(func.count())
            .select_from(Scene)
            .where(and_(Scene.is_public.is_(True), Scene.is_deleted.is_(False)))
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def search(
        self, query: str, tag: str | None, offset: int, limit: int
    ) -> list[Scene]:
        """模糊搜索公开场景（按名称/描述/元数据），可选 tag 过滤。"""
        conditions = [
            Scene.is_public.is_(True),
            Scene.is_deleted.is_(False),
            or_(
                Scene.name.ilike(f"%{query}%"),
                Scene.description.ilike(f"%{query}%"),
                Scene.genre.ilike(f"%{query}%"),
                Scene.time_period.ilike(f"%{query}%"),
                Scene.setting_location.ilike(f"%{query}%"),
                Scene.mood.ilike(f"%{query}%"),
            ),
        ]
        if tag:
            conditions.append(Scene.tags.op("@>")(f'["{tag}"]'))

        stmt = (
            select(Scene)
            .where(and_(*conditions))
            .order_by(desc(Scene.play_count), desc(Scene.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_search(self, query: str, tag: str | None) -> int:
        """统计搜索结果总数。"""
        conditions = [
            Scene.is_public.is_(True),
            Scene.is_deleted.is_(False),
            or_(
                Scene.name.ilike(f"%{query}%"),
                Scene.description.ilike(f"%{query}%"),
                Scene.genre.ilike(f"%{query}%"),
                Scene.time_period.ilike(f"%{query}%"),
                Scene.setting_location.ilike(f"%{query}%"),
                Scene.mood.ilike(f"%{query}%"),
            ),
        ]
        if tag:
            conditions.append(Scene.tags.op("@>")(f'["{tag}"]'))

        stmt = select(func.count()).select_from(Scene).where(and_(*conditions))
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def update(self, scene_id: str, **kwargs) -> Scene:
        """更新场景。"""
        scene = await self.get_by_id(scene_id)
        if not scene:
            raise ValueError(f"场景不存在: {scene_id}")

        for key, value in kwargs.items():
            if hasattr(scene, key):
                setattr(scene, key, value)

        await self._session.flush()
        await self._session.refresh(scene)
        return scene

    async def soft_delete(self, scene_id: str) -> None:
        """软删除场景。"""
        scene = await self.get_by_id(scene_id)
        if scene:
            scene.is_deleted = True
            scene.deleted_at = func.now()
            await self._session.flush()

    async def hard_delete(self, scene_id: str) -> None:
        """硬删除场景。"""
        scene = await self.get_by_id(scene_id)
        if scene:
            await self._session.delete(scene)
            await self._session.flush()

    async def add_character(
        self, scene_id: str, character_id: str, role_in_scene: str, sort_order: int
    ) -> None:
        """向场景添加角色。"""
        scene_character = SceneCharacter(
            scene_id=scene_id,
            character_id=character_id,
            role_in_scene=role_in_scene,
            sort_order=sort_order,
        )
        self._session.add(scene_character)
        await self._session.flush()

    async def remove_character(self, scene_id: str, character_id: str) -> None:
        """从场景移除角色。"""
        stmt = select(SceneCharacter).where(
            and_(
                SceneCharacter.scene_id == scene_id,
                SceneCharacter.character_id == character_id,
            )
        )
        result = await self._session.execute(stmt)
        scene_character = result.scalar_one_or_none()
        if scene_character:
            await self._session.delete(scene_character)
            await self._session.flush()

    async def get_scene_characters(self, scene_id: str) -> list[SceneCharacter]:
        """获取场景关联的所有角色。"""
        stmt = (
            select(SceneCharacter)
            .where(SceneCharacter.scene_id == scene_id)
            .order_by(SceneCharacter.sort_order)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_scene_characters(self, scene_id: str) -> int:
        """统计场景关联的角色数量。"""
        stmt = (
            select(func.count())
            .select_from(SceneCharacter)
            .where(SceneCharacter.scene_id == scene_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def increment_play_count(self, scene_id: str) -> None:
        """增加场景游玩计数。"""
        scene = await self.get_by_id(scene_id)
        if scene:
            scene.play_count += 1
            await self._session.flush()

    async def get_with_creator(self, scene_id: str) -> Scene | None:
        """获取场景及其创建者信息（JOIN users）。"""
        stmt = (
            select(Scene)
            .join(User, Scene.creator_id == User.id)
            .where(and_(Scene.id == scene_id, Scene.is_deleted.is_(False)))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
