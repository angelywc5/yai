"""角色数据访问层。"""

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.models import Character, User
from src.utils.id_generator import new_id


class CharacterRepository:
    """角色数据访问。"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        name: str,
        definition: dict,
        creator_id: str,
        avatar_url: str | None,
        avatar_source: str,
        tagline: str,
        tags: list[str],
        is_public: bool,
    ) -> Character:
        """创建角色。"""
        character = Character(
            id=new_id(),
            name=name,
            definition=definition,
            creator_id=creator_id,
            avatar_url=avatar_url,
            avatar_source=avatar_source,
            tagline=tagline,
            tags=tags,
            is_public=is_public,
        )
        self._session.add(character)
        await self._session.flush()
        await self._session.refresh(character, attribute_names=["creator"])
        return character

    async def get_by_id(self, character_id: str) -> Character | None:
        """根据 ID 获取角色（不过滤软删除）。"""
        stmt = select(Character).where(Character.id == character_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_active(self, character_id: str) -> Character | None:
        """根据 ID 获取角色（过滤软删除），eager load creator。"""
        stmt = (
            select(Character)
            .options(selectinload(Character.creator))
            .where(
                and_(Character.id == character_id, Character.is_deleted.is_(False))
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_creator(
        self, creator_id: str, offset: int, limit: int
    ) -> list[Character]:
        """获取创建者的所有角色（含软删除），eager load creator。"""
        stmt = (
            select(Character)
            .options(selectinload(Character.creator))
            .where(Character.creator_id == creator_id)
            .order_by(desc(Character.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_creator(self, creator_id: str) -> int:
        """统计创建者的角色总数（含软删除）。"""
        stmt = (
            select(func.count())
            .select_from(Character)
            .where(Character.creator_id == creator_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_public(
        self, offset: int, limit: int, sort: str = "popular"
    ) -> list[Character]:
        """
        获取公开角色列表，支持排序：
        - popular: 按 chat_count DESC
        - newest: 按 created_at DESC
        - most_chats: 按 chat_count DESC
        """
        order_clause = (
            desc(Character.created_at)
            if sort == "newest"
            else desc(Character.chat_count)
        )
        stmt = (
            select(Character)
            .options(selectinload(Character.creator))
            .where(and_(Character.is_public.is_(True), Character.is_deleted.is_(False)))
            .order_by(order_clause, desc(Character.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_public(self) -> int:
        """统计公开角色总数。"""
        stmt = (
            select(func.count())
            .select_from(Character)
            .where(and_(Character.is_public.is_(True), Character.is_deleted.is_(False)))
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def search(
        self, query: str, tag: str | None, offset: int, limit: int
    ) -> list[Character]:
        """模糊搜索公开角色（按名称/宣传语），可选 tag 过滤。"""
        conditions = [
            Character.is_public.is_(True),
            Character.is_deleted.is_(False),
            or_(
                Character.name.ilike(f"%{query}%"),
                Character.tagline.ilike(f"%{query}%"),
            ),
        ]
        if tag:
            conditions.append(Character.tags.op("@>")(f'["{tag}"]'))

        stmt = (
            select(Character)
            .options(selectinload(Character.creator))
            .where(and_(*conditions))
            .order_by(desc(Character.chat_count), desc(Character.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_search(self, query: str, tag: str | None) -> int:
        """统计搜索结果总数。"""
        conditions = [
            Character.is_public.is_(True),
            Character.is_deleted.is_(False),
            or_(
                Character.name.ilike(f"%{query}%"),
                Character.tagline.ilike(f"%{query}%"),
            ),
        ]
        if tag:
            conditions.append(Character.tags.op("@>")(f'["{tag}"]'))

        stmt = select(func.count()).select_from(Character).where(and_(*conditions))
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def update(self, character_id: str, **kwargs) -> Character:
        """更新角色。"""
        character = await self.get_by_id(character_id)
        if not character:
            raise ValueError(f"角色不存在: {character_id}")

        for key, value in kwargs.items():
            if hasattr(character, key):
                setattr(character, key, value)

        await self._session.flush()
        await self._session.refresh(character, attribute_names=["creator"])
        return character

    async def soft_delete(self, character_id: str) -> None:
        """软删除角色。"""
        character = await self.get_by_id(character_id)
        if character:
            character.is_deleted = True
            character.deleted_at = func.now()
            await self._session.flush()

    async def hard_delete(self, character_id: str) -> None:
        """硬删除角色。"""
        character = await self.get_by_id(character_id)
        if character:
            await self._session.delete(character)
            await self._session.flush()

    async def increment_chat_count(self, character_id: str) -> None:
        """增加对话计数。"""
        character = await self.get_by_id(character_id)
        if character:
            character.chat_count += 1
            await self._session.flush()

    async def increment_like_count(self, character_id: str) -> None:
        """增加点赞计数。"""
        character = await self.get_by_id(character_id)
        if character:
            character.like_count += 1
            await self._session.flush()

    async def get_with_creator(self, character_id: str) -> Character | None:
        """获取角色及其创建者信息（JOIN users）。"""
        stmt = (
            select(Character)
            .join(User, Character.creator_id == User.id)
            .where(and_(Character.id == character_id, Character.is_deleted.is_(False)))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
