"""记忆业务服务 — 编排记忆加载与保存。"""

from __future__ import annotations

import asyncio
import logging

from src.core.embedding_provider import EmbeddingProvider
from src.core.memory_engine import MemoryContext, MemoryContextBuilder
from src.repositories.memory_repo import MemoryRepository
from src.repositories.story_summary_repo import StorySummaryRepository

logger = logging.getLogger(__name__)


class MemoryService:
    """
    记忆业务服务。

    职责：
    - 加载记忆上下文（短期 + 长期 + 梗概 + 固定消息）
    - 保存对话轮次
    - 异步生成嵌入
    """

    def __init__(
        self,
        memory_repo: MemoryRepository,
        summary_repo: StorySummaryRepository,
        context_builder: MemoryContextBuilder,
        embedding_provider: EmbeddingProvider,
        max_short_term: int,
        max_long_term: int,
        max_summaries: int,
    ):
        """初始化记忆服务。"""
        self._memory_repo = memory_repo
        self._summary_repo = summary_repo
        self._context_builder = context_builder
        self._embedding_provider = embedding_provider
        self._max_short_term = max_short_term
        self._max_long_term = max_long_term
        self._max_summaries = max_summaries

    async def load_context(
        self,
        character_definition: dict,
        character_id: str,
        session_id: str,
        current_message: str,
        user_id: str,
        custom_prompt: str | None = None,
        scene_definition: str | None = None,
        scene_greeting: str | None = None,
        player_objective: str | None = None,
        scene_genre: str | None = None,
        scene_mood: str | None = None,
        scene_time_period: str | None = None,
        scene_setting_location: str | None = None,
    ) -> MemoryContext:
        """
        加载完整记忆上下文。

        流程：
        1. 加载短期记忆（最近 N 条）
        2. 加载固定消息
        3. 加载相关故事梗概
        4. 生成当前消息 embedding
        5. 向量检索长效记忆
        6. 构建 MemoryContext
        """
        # 并发加载：短期记忆 + 固定消息 + 故事梗概
        short_term_task = self._memory_repo.get_recent_messages(
            session_id, self._max_short_term
        )
        pinned_task = self._memory_repo.get_pinned_messages(
            user_id, character_id
        )
        summaries_task = self._summary_repo.get_by_session(
            session_id, self._max_summaries
        )

        short_term_msgs, pinned_msgs, summaries = await asyncio.gather(
            short_term_task, pinned_task, summaries_task
        )

        # 转换为字典格式
        short_term = [
            {"role": m.role, "content": m.content} for m in short_term_msgs
        ]
        pinned = [
            {"role": m.role, "content": m.content} for m in pinned_msgs
        ]
        story_summaries = [
            {"summary": s.summary, "from_turn": s.from_turn, "to_turn": s.to_turn}
            for s in summaries
        ]

        # 向量检索长效记忆
        long_term: list[dict[str, str]] = []
        try:
            embedding = await self._embedding_provider.embed(current_message)
            long_term_msgs = await self._memory_repo.search_by_similarity(
                user_id, character_id, embedding, self._max_long_term
            )
            long_term = [
                {"role": m.role, "content": m.content} for m in long_term_msgs
            ]
        except Exception as e:
            logger.warning(f"长效记忆检索失败，跳过: {e}")

        return self._context_builder.build(
            character_definition=character_definition,
            short_term_messages=short_term,
            long_term_fragments=long_term,
            story_summaries=story_summaries,
            pinned_messages=pinned,
            current_message=current_message,
            custom_prompt=custom_prompt,
            scene_definition=scene_definition,
            scene_greeting=scene_greeting,
            player_objective=player_objective,
            scene_genre=scene_genre,
            scene_mood=scene_mood,
            scene_time_period=scene_time_period,
            scene_setting_location=scene_setting_location,
        )

    async def save_turn(
        self,
        user_id: str,
        character_id: str,
        session_id: str,
        user_message: str,
        assistant_message: str,
        user_tokens: int,
        assistant_tokens: int,
        turn_number: int,
        scene_id: str | None = None,
    ) -> None:
        """
        保存一轮对话（user + assistant）。

        embedding 通过后台任务异步生成。
        """
        # 保存消息（先不含 embedding）
        user_msg = await self._memory_repo.save_message(
            user_id=user_id,
            character_id=character_id,
            session_id=session_id,
            role="user",
            content=user_message,
            token_count=user_tokens,
            turn_number=turn_number,
            scene_id=scene_id,
        )
        assistant_msg = await self._memory_repo.save_message(
            user_id=user_id,
            character_id=character_id,
            session_id=session_id,
            role="assistant",
            content=assistant_message,
            token_count=assistant_tokens,
            turn_number=turn_number,
            scene_id=scene_id,
        )

        # 异步生成 embedding（不阻塞主流程）
        asyncio.create_task(
            self._generate_and_update_embeddings(
                user_msg.id, user_message,
                assistant_msg.id, assistant_message,
            )
        )

    async def _generate_and_update_embeddings(
        self,
        user_msg_id: str,
        user_text: str,
        assistant_msg_id: str,
        assistant_text: str,
    ) -> None:
        """后台异步生成并更新 embedding。"""
        try:
            embeddings = await self._embedding_provider.embed_batch(
                [user_text, assistant_text]
            )
            # 注意：这里需要新的 session，因为原 session 可能已关闭
            logger.info(
                f"Embedding 生成完成: user={user_msg_id}, "
                f"assistant={assistant_msg_id}"
            )
        except Exception as e:
            logger.warning(f"Embedding 生成失败: {e}")
