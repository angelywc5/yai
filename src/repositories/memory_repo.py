"""消息与记忆数据访问层。"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    and_,
    delete,
    desc,
    func,
    select,
    text,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Message
from src.utils.id_generator import generate_cuid


class MemoryRepository:
    """消息与记忆数据访问。"""

    def __init__(self, session: AsyncSession):
        """初始化 Repository。"""
        self.session = session

    # ---- 消息 CRUD ----

    async def save_message(
        self,
        user_id: str,
        character_id: str,
        session_id: str,
        role: str,
        content: str,
        token_count: int,
        turn_number: int,
        scene_id: str | None = None,
        embedding: list[float] | None = None,
    ) -> Message:
        """
        保存消息。

        Args:
            user_id: 用户 ID
            character_id: 角色 ID
            session_id: 会话 ID
            role: 消息角色（user/assistant）
            content: 消息内容
            token_count: Token 数量
            turn_number: 对话轮次
            scene_id: 场景 ID（可选）
            embedding: 向量嵌入（可选）

        Returns:
            创建的消息
        """
        message = Message(
            id=generate_cuid(),
            user_id=user_id,
            character_id=character_id,
            session_id=session_id,
            role=role,
            content=content,
            token_count=token_count,
            turn_number=turn_number,
            scene_id=scene_id,
            embedding=embedding,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_recent_messages(
        self, session_id: str, limit: int
    ) -> list[Message]:
        """
        按 created_at ASC 查询最近 N 条消息（排除 is_deleted）。

        注意：返回的消息按时间正序（旧到新），便于直接构建上下文。
        """
        subq = (
            select(Message.id)
            .where(Message.session_id == session_id, Message.is_deleted == False)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        stmt = (
            select(Message)
            .where(Message.id.in_(subq))
            .order_by(Message.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_current_turn_number(self, session_id: str) -> int:
        """获取当前会话的最大轮次号。"""
        stmt = (
            select(func.max(Message.turn_number))
            .where(Message.session_id == session_id, Message.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_messages_by_turn_range(
        self, session_id: str, from_turn: int, to_turn: int
    ) -> list[Message]:
        """按轮次范围查询消息（用于故事梗概生成）。"""
        stmt = (
            select(Message)
            .where(
                Message.session_id == session_id,
                Message.turn_number >= from_turn,
                Message.turn_number <= to_turn,
                Message.is_deleted == False,
            )
            .order_by(Message.turn_number, Message.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_similarity(
        self,
        user_id: str,
        character_id: str,
        embedding: list[float],
        limit: int,
    ) -> list[Message]:
        """
        pgvector 余弦相似度检索。

        仅检索有 embedding 且未删除的消息。
        """
        stmt = (
            select(Message)
            .where(
                Message.user_id == user_id,
                Message.character_id == character_id,
                Message.is_deleted == False,
                Message.embedding.isnot(None),
            )
            .order_by(Message.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---- 会话历史 ----

    async def get_session_history(
        self,
        session_id: str,
        before_message_id: str | None = None,
        limit: int = 40,
    ) -> list[Message]:
        """
        获取会话历史（分页，按时间倒序）。

        Args:
            session_id: 会话 ID
            before_message_id: 游标（获取此消息之前的记录）
            limit: 每页条数

        Returns:
            消息列表（按时间倒序）
        """
        conditions = [
            Message.session_id == session_id,
            Message.is_deleted == False,
        ]

        if before_message_id:
            subq = select(Message.created_at).where(
                Message.id == before_message_id
            )
            conditions.append(Message.created_at < subq.scalar_subquery())

        stmt = (
            select(Message)
            .where(*conditions)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---- 消息操作 ----

    async def get_message_by_id(
        self, message_id: str, user_id: str
    ) -> Message | None:
        """按 ID 获取消息（校验 user_id 归属）。"""
        stmt = select(Message).where(
            Message.id == message_id,
            Message.user_id == user_id,
            Message.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_message_content(
        self, message_id: str, content: str
    ) -> None:
        """更新消息内容。"""
        stmt = (
            update(Message)
            .where(Message.id == message_id)
            .values(content=content)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def soft_delete_message(self, message_id: str) -> None:
        """软删除消息。"""
        stmt = (
            update(Message)
            .where(Message.id == message_id)
            .values(is_deleted=True)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def soft_delete_messages_after_turn(
        self, session_id: str, turn_number: int
    ) -> int:
        """软删除某轮次之后的所有消息（倒带），返回删除数量。"""
        stmt = (
            update(Message)
            .where(
                Message.session_id == session_id,
                Message.turn_number > turn_number,
                Message.is_deleted == False,
            )
            .values(is_deleted=True)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount or 0

    async def update_message_feedback(
        self, message_id: str, feedback: str | None
    ) -> None:
        """更新消息反馈（like/dislike/null）。"""
        stmt = (
            update(Message)
            .where(Message.id == message_id)
            .values(feedback=feedback)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def toggle_message_pin(
        self, message_id: str, is_pinned: bool
    ) -> None:
        """切换消息固定状态。"""
        stmt = (
            update(Message)
            .where(Message.id == message_id)
            .values(is_pinned=is_pinned)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_pinned_messages(
        self, user_id: str, character_id: str
    ) -> list[Message]:
        """获取用户对某角色固定的所有消息。"""
        stmt = (
            select(Message)
            .where(
                Message.user_id == user_id,
                Message.character_id == character_id,
                Message.is_pinned == True,
                Message.is_deleted == False,
            )
            .order_by(Message.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def copy_messages_to_new_session(
        self,
        source_session_id: str,
        up_to_turn: int,
        new_session_id: str,
    ) -> int:
        """
        复制消息到新会话（分叉功能）。

        使用 INSERT ... SELECT 批量复制。

        Returns:
            复制的消息数量
        """
        source_messages = (
            select(Message)
            .where(
                Message.session_id == source_session_id,
                Message.turn_number <= up_to_turn,
                Message.is_deleted == False,
            )
            .order_by(Message.created_at)
        )
        result = await self.session.execute(source_messages)
        messages = list(result.scalars().all())

        count = 0
        for msg in messages:
            new_msg = Message(
                id=generate_cuid(),
                user_id=msg.user_id,
                character_id=msg.character_id,
                session_id=new_session_id,
                role=msg.role,
                content=msg.content,
                token_count=msg.token_count,
                turn_number=msg.turn_number,
                scene_id=msg.scene_id,
                embedding=msg.embedding,
            )
            self.session.add(new_msg)
            count += 1

        await self.session.flush()
        return count

    # ---- 会话管理 ----

    async def get_user_sessions(
        self,
        user_id: str,
        character_id: str,
        offset: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        """
        获取用户与某角色的会话列表。

        返回: [{session_id, last_message_content, last_message_at, message_count}]
        """
        stmt = (
            select(
                Message.session_id,
                func.max(Message.content).label("last_message_content"),
                func.max(Message.created_at).label("last_message_at"),
                func.count(Message.id).label("message_count"),
            )
            .where(
                Message.user_id == user_id,
                Message.character_id == character_id,
                Message.is_deleted == False,
            )
            .group_by(Message.session_id)
            .order_by(desc(func.max(Message.created_at)))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "session_id": row.session_id,
                "last_message_content": row.last_message_content,
                "last_message_at": row.last_message_at,
                "message_count": row.message_count,
            }
            for row in rows
        ]

    async def delete_session(self, session_id: str, user_id: str) -> None:
        """删除整个会话（软删除所有消息）。"""
        stmt = (
            update(Message)
            .where(
                Message.session_id == session_id,
                Message.user_id == user_id,
            )
            .values(is_deleted=True)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_recent_character_sessions(
        self, user_id: str, limit: int = 20
    ) -> list[dict]:
        """
        获取用户最近对话过的角色列表（左侧导航用）。

        返回去重后的角色列表，按最近对话时间排序。
        """
        stmt = text("""
            SELECT DISTINCT ON (character_id)
                character_id, session_id, content, created_at
            FROM messages
            WHERE user_id = :user_id AND is_deleted = false
            ORDER BY character_id, created_at DESC
        """)
        result = await self.session.execute(stmt, {"user_id": user_id})
        rows = result.all()

        # 按 created_at 倒序排列
        sorted_rows = sorted(rows, key=lambda r: r.created_at, reverse=True)
        return [
            {
                "character_id": row.character_id,
                "session_id": row.session_id,
                "last_message_content": row.content,
                "last_message_at": row.created_at,
            }
            for row in sorted_rows[:limit]
        ]
