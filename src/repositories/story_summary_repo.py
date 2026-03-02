"""故事梗概数据访问层。"""

from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import StorySummary
from src.utils.id_generator import generate_cuid


class StorySummaryRepository:
    """故事梗概数据访问。"""

    def __init__(self, session: AsyncSession):
        """初始化 Repository。"""
        self.session = session

    async def create(
        self,
        session_id: str,
        user_id: str,
        character_id: str,
        from_turn: int,
        to_turn: int,
        summary: str,
        key_dialogues: str,
        scene_id: str | None = None,
        embedding: list[float] | None = None,
    ) -> StorySummary:
        """
        创建故事梗概。

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            character_id: 角色 ID
            from_turn: 摘要起始轮次
            to_turn: 摘要结束轮次
            summary: 摘要文本
            key_dialogues: 关键对话（YAML 格式字符串）
            scene_id: 场景 ID（可选）
            embedding: 向量嵌入（可选）

        Returns:
            创建的故事梗概
        """
        story_summary = StorySummary(
            id=generate_cuid(),
            session_id=session_id,
            user_id=user_id,
            character_id=character_id,
            from_turn=from_turn,
            to_turn=to_turn,
            summary=summary,
            key_dialogues=key_dialogues,
            scene_id=scene_id,
            embedding=embedding,
        )
        self.session.add(story_summary)
        await self.session.flush()
        return story_summary

    async def get_by_session(
        self, session_id: str, limit: int
    ) -> list[StorySummary]:
        """
        获取会话最近的故事梗概。

        Args:
            session_id: 会话 ID
            limit: 最大数量

        Returns:
            梗概列表（按创建时间倒序）
        """
        stmt = (
            select(StorySummary)
            .where(StorySummary.session_id == session_id)
            .order_by(desc(StorySummary.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_last_summary_turn(self, session_id: str) -> int:
        """
        获取最后一次梗概的结束轮次。

        Args:
            session_id: 会话 ID

        Returns:
            最后梗概的 to_turn，无梗概时返回 0
        """
        stmt = (
            select(func.max(StorySummary.to_turn))
            .where(StorySummary.session_id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def search_by_similarity(
        self,
        user_id: str,
        embedding: list[float],
        limit: int,
    ) -> list[StorySummary]:
        """
        跨会话的故事梗概语义检索。

        Args:
            user_id: 用户 ID
            embedding: 查询向量
            limit: 最大数量

        Returns:
            语义相关的梗概列表
        """
        stmt = (
            select(StorySummary)
            .where(
                StorySummary.user_id == user_id,
                StorySummary.embedding.isnot(None),
            )
            .order_by(StorySummary.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
