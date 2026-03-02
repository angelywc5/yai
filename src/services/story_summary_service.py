"""故事梗概服务 — 编排梗概触发与生成。"""

from __future__ import annotations

import asyncio
import logging

import yaml

from src.core.embedding_provider import EmbeddingProvider
from src.core.model_provider import ModelConfig, ModelProvider, StreamChunk
from src.core.models import StorySummary
from src.core.schemas import ModelTier
from src.core.story_summary_engine import StorySummaryEngine
from src.core.yaml_parser import YamlResponseParser
from src.repositories.memory_repo import MemoryRepository
from src.repositories.story_summary_repo import StorySummaryRepository

logger = logging.getLogger(__name__)


class StorySummaryService:
    """
    故事梗概服务。

    职责：
    - 检查是否需要生成梗概
    - 调用 AI 生成梗概（YAML 格式）
    - 解析并存储梗概 + 向量嵌入
    """

    def __init__(
        self,
        summary_engine: StorySummaryEngine,
        summary_repo: StorySummaryRepository,
        memory_repo: MemoryRepository,
        model_provider: ModelProvider,
        embedding_provider: EmbeddingProvider,
        summary_model_tier: str = "speed",
    ):
        """初始化梗概服务。"""
        self._engine = summary_engine
        self._summary_repo = summary_repo
        self._memory_repo = memory_repo
        self._model_provider = model_provider
        self._embedding_provider = embedding_provider
        self._summary_model_tier = summary_model_tier

    async def check_and_generate(
        self,
        session_id: str,
        user_id: str,
        character_id: str,
        current_turn: int,
        character_name: str,
        scene_id: str | None = None,
    ) -> StorySummary | None:
        """
        检查是否需要生成梗概。

        如果需要，异步生成并存储。

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            character_id: 角色 ID
            current_turn: 当前轮次
            character_name: 角色名称
            scene_id: 场景 ID（可选）

        Returns:
            生成的 StorySummary，或 None（不需要/失败）
        """
        last_turn = await self._summary_repo.get_last_summary_turn(session_id)

        if not self._engine.should_trigger(current_turn, last_turn):
            return None

        # 获取需要总结的消息
        from_turn = last_turn + 1
        to_turn = current_turn
        messages = await self._memory_repo.get_messages_by_turn_range(
            session_id, from_turn, to_turn
        )

        if not messages:
            return None

        # 构建 prompt
        msg_dicts = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        prompt = self._engine.build_summary_prompt(msg_dicts, character_name)

        # 调用 AI 生成梗概
        try:
            summary_text = await self._generate_summary(prompt)
            parsed = self._parse_summary(summary_text)

            # 生成嵌入
            embedding = None
            try:
                embedding = await self._embedding_provider.embed(
                    parsed["summary"]
                )
            except Exception as e:
                logger.warning(f"梗概嵌入生成失败: {e}")

            # 存储
            story_summary = await self._summary_repo.create(
                session_id=session_id,
                user_id=user_id,
                character_id=character_id,
                from_turn=from_turn,
                to_turn=to_turn,
                summary=parsed["summary"],
                key_dialogues=parsed["key_dialogues"],
                scene_id=scene_id,
                embedding=embedding,
            )

            logger.info(
                f"故事梗概生成: session={session_id}, "
                f"turns={from_turn}-{to_turn}"
            )
            return story_summary

        except Exception as e:
            logger.error(f"故事梗概生成失败: {e}")
            return None

    async def _generate_summary(self, prompt: str) -> str:
        """调用 AI 生成梗概文本。"""
        config = ModelConfig(
            tier=ModelTier(self._summary_model_tier),
            model_name="",
            credits_per_1k_tokens=0,
        )
        messages = [
            {"role": "system", "content": "你是一个故事摘要生成器。"},
            {"role": "user", "content": prompt},
        ]

        accumulated = ""
        async for chunk in self._model_provider.stream_chat(messages, config):
            if chunk.content:
                accumulated += chunk.content

        return accumulated

    def _parse_summary(self, text: str) -> dict[str, str]:
        """解析 YAML 格式的梗概。"""
        cleaned = text.strip()
        if cleaned.startswith("```yaml"):
            cleaned = cleaned[len("```yaml"):]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        if cleaned.startswith("---"):
            cleaned = cleaned[3:]
        cleaned = cleaned.strip()

        try:
            result = yaml.safe_load(cleaned)
            if isinstance(result, dict):
                summary = str(result.get("summary", "")).strip()
                key_dialogues = result.get("key_dialogues", [])
                if isinstance(key_dialogues, list):
                    key_dialogues_str = yaml.dump(
                        key_dialogues,
                        allow_unicode=True,
                        default_flow_style=False,
                    )
                else:
                    key_dialogues_str = str(key_dialogues)
                return {
                    "summary": summary,
                    "key_dialogues": key_dialogues_str,
                }
        except yaml.YAMLError as e:
            logger.warning(f"梗概 YAML 解析失败: {e}")

        return {"summary": text.strip(), "key_dialogues": ""}
