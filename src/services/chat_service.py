"""对话编排服务 — 核心业务流程。"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    InsufficientCreditsError,
    MessageEditNotAllowedError,
    MessageFeedbackNotAllowedError,
    MessageNotFoundError,
    MessagePermissionError,
    ModelProviderError,
)
from src.core.model_provider import ModelConfig, ModelProvider
from src.core.schemas import (
    ChatRequest,
    MessageEditRequest,
    MessageRegenerateRequest,
    ModelTier,
)
from src.core.yaml_parser import YamlResponseParser
from src.repositories.memory_repo import MemoryRepository
from src.services.character_service import CharacterService
from src.services.credit_service import CreditService
from src.services.memory_service import MemoryService
from src.services.scene_service import SceneService
from src.services.story_summary_service import StorySummaryService
from src.utils.id_generator import generate_cuid

logger = logging.getLogger(__name__)


class ChatService:
    """
    对话编排服务。

    编排完整对话流程：
    加载角色 → 加载记忆 → 预扣积分 → 流式调用模型 → 结算积分 → 保存消息
    """

    def __init__(
        self,
        character_service: CharacterService,
        scene_service: SceneService,
        memory_service: MemoryService,
        credit_service: CreditService,
        model_provider: ModelProvider,
        yaml_parser: YamlResponseParser,
        story_summary_service: StorySummaryService,
        memory_repo: MemoryRepository,
    ):
        """初始化对话服务。"""
        self._character_service = character_service
        self._scene_service = scene_service
        self._memory_service = memory_service
        self._credit_service = credit_service
        self._model_provider = model_provider
        self._yaml_parser = yaml_parser
        self._story_summary_service = story_summary_service
        self._memory_repo = memory_repo

    async def stream_chat(
        self,
        session: AsyncSession,
        user_id: str,
        request: ChatRequest,
    ) -> AsyncGenerator[dict, None]:
        """
        完整对话流程（SSE 流式输出）。

        Yields:
            SSE 事件字典：
            - {"type": "token", "content": "..."}
            - {"type": "action", "content": "..."}
            - {"type": "done", ...}
            - {"type": "error", ...}
        """
        # 1. 加载角色
        character = await self._character_service.get_character(
            session, request.character_id, user_id
        )
        char_definition = character.definition or {}
        char_name = character.name

        # 2. 加载场景（可选）
        scene_kwargs: dict = {}
        if request.scene_id:
            scene = await self._scene_service.get_scene(
                session, request.scene_id, user_id
            )
            scene_kwargs = {
                "scene_definition": scene.scene_definition,
                "scene_greeting": scene.greeting,
                "player_objective": scene.player_objective,
                "scene_genre": scene.genre,
                "scene_mood": scene.mood,
                "scene_time_period": scene.time_period,
                "scene_setting_location": scene.setting_location,
            }

        # 3. 确定会话 ID
        session_id = request.session_id or generate_cuid()

        # 4. 获取当前轮次
        current_turn = await self._memory_repo.get_current_turn_number(
            session_id
        )
        new_turn = current_turn + 1

        # 5. 构建用户消息（含指令）
        user_message = self._build_user_message(request)

        # 6. 加载记忆上下文
        memory_context = await self._memory_service.load_context(
            character_definition=char_definition,
            character_id=request.character_id,
            session_id=session_id,
            current_message=user_message,
            user_id=user_id,
            **scene_kwargs,
        )

        # 7. 构建消息列表
        messages = memory_context.build_messages()
        messages.append({"role": "user", "content": user_message})

        # 8. 预扣积分
        tier = request.model_tier or ModelTier.SPEED
        try:
            hold = await self._credit_service.hold_credits(
                session, user_id, tier
            )
        except InsufficientCreditsError as e:
            yield {
                "type": "error",
                "message": e.message,
                "code": e.code,
            }
            return

        # 9. 流式调用模型
        config = ModelConfig(tier=tier, model_name="", credits_per_1k_tokens=0)
        accumulated_text = ""
        total_tokens = 0

        try:
            async for chunk in self._model_provider.stream_chat(
                messages, config
            ):
                if chunk.content:
                    accumulated_text += chunk.content

                    # 尝试从流式文本提取 speech
                    speech = self._yaml_parser.extract_speech_from_stream(
                        accumulated_text
                    )
                    if speech:
                        yield {"type": "token", "content": chunk.content}

                if chunk.is_final:
                    total_tokens = chunk.total_tokens

        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            await self._credit_service.rollback_hold(session, hold)
            await session.commit()
            yield {
                "type": "error",
                "message": f"模型调用异常: {str(e)}",
                "code": "MODEL_PROVIDER_ERROR",
            }
            return

        # 10. 解析 YAML 响应
        yaml_response = self._yaml_parser.parse_final(accumulated_text)
        stored_content = self._yaml_parser.format_for_storage(yaml_response)

        # 11. 结算积分
        settlement = await self._credit_service.settle_credits(
            session, hold, total_tokens
        )

        # 12. 保存消息
        await self._memory_service.save_turn(
            user_id=user_id,
            character_id=request.character_id,
            session_id=session_id,
            user_message=user_message,
            assistant_message=stored_content,
            user_tokens=0,
            assistant_tokens=total_tokens,
            turn_number=new_turn,
            scene_id=request.scene_id,
        )

        await session.commit()

        # 13. 输出 action 事件（如果有）
        if yaml_response.action:
            yield {
                "type": "action",
                "content": yaml_response.action,
            }

        # 14. 输出 done 事件
        yield {
            "type": "done",
            "schema_version": yaml_response.schema_version,
            "speech": yaml_response.speech,
            "action": yaml_response.action,
            "emotion": yaml_response.emotion,
            "tokens_used": total_tokens,
            "credits_deducted": settlement.actual_amount,
            "session_id": session_id,
        }

        # 15. 异步生成故事梗概
        asyncio.create_task(
            self._story_summary_service.check_and_generate(
                session_id=session_id,
                user_id=user_id,
                character_id=request.character_id,
                current_turn=new_turn,
                character_name=char_name,
                scene_id=request.scene_id,
            )
        )

    # ---- 消息操作 ----

    async def edit_message(
        self,
        session: AsyncSession,
        user_id: str,
        message_id: str,
        request: MessageEditRequest,
    ) -> AsyncGenerator[dict, None]:
        """编辑用户消息并重新生成 AI 回复。"""
        msg = await self._memory_repo.get_message_by_id(message_id, user_id)
        if not msg:
            raise MessageNotFoundError(message_id)
        if msg.role != "user":
            raise MessageEditNotAllowedError()

        # 更新消息内容
        await self._memory_repo.update_message_content(
            message_id, request.content
        )

        # 软删除之后的消息（倒带）
        await self._memory_repo.soft_delete_messages_after_turn(
            msg.session_id, msg.turn_number
        )

        # 用新内容重新生成
        new_request = ChatRequest(
            character_id=msg.character_id,
            message=request.content,
            model_tier=request.model_tier,
            session_id=msg.session_id,
            scene_id=msg.scene_id,
        )

        async for event in self.stream_chat(session, user_id, new_request):
            yield event

    async def regenerate_message(
        self,
        session: AsyncSession,
        user_id: str,
        message_id: str,
        request: MessageRegenerateRequest,
    ) -> AsyncGenerator[dict, None]:
        """重新生成 AI 回复。"""
        msg = await self._memory_repo.get_message_by_id(message_id, user_id)
        if not msg:
            raise MessageNotFoundError(message_id)
        if msg.role != "assistant":
            raise MessageEditNotAllowedError()

        # 软删除当前 AI 回复
        await self._memory_repo.soft_delete_message(message_id)

        # 找到对应的用户消息
        recent = await self._memory_repo.get_recent_messages(
            msg.session_id, limit=5
        )
        user_msg_content = ""
        for m in reversed(recent):
            if m.role == "user" and m.turn_number == msg.turn_number:
                user_msg_content = m.content
                break

        if not user_msg_content:
            user_msg_content = "继续"

        new_request = ChatRequest(
            character_id=msg.character_id,
            message=user_msg_content,
            model_tier=request.model_tier,
            session_id=msg.session_id,
            scene_id=msg.scene_id,
        )

        async for event in self.stream_chat(session, user_id, new_request):
            yield event

    async def delete_message(
        self, session: AsyncSession, user_id: str, message_id: str
    ) -> None:
        """软删除单条消息。"""
        msg = await self._memory_repo.get_message_by_id(message_id, user_id)
        if not msg:
            raise MessageNotFoundError(message_id)
        await self._memory_repo.soft_delete_message(message_id)
        await session.commit()

    async def rewind_to_message(
        self, session: AsyncSession, user_id: str, message_id: str
    ) -> int:
        """倒带到某条消息，返回被删除的消息数量。"""
        msg = await self._memory_repo.get_message_by_id(message_id, user_id)
        if not msg:
            raise MessageNotFoundError(message_id)
        count = await self._memory_repo.soft_delete_messages_after_turn(
            msg.session_id, msg.turn_number
        )
        await session.commit()
        return count

    async def fork_from_message(
        self,
        session: AsyncSession,
        user_id: str,
        message_id: str,
        model_tier: ModelTier | None = None,
    ) -> AsyncGenerator[dict, None]:
        """从某条消息处分叉出新会话。"""
        msg = await self._memory_repo.get_message_by_id(message_id, user_id)
        if not msg:
            raise MessageNotFoundError(message_id)

        new_session_id = generate_cuid()
        await self._memory_repo.copy_messages_to_new_session(
            msg.session_id, msg.turn_number, new_session_id
        )

        # 找最后一条 user 消息
        user_msg_content = ""
        recent = await self._memory_repo.get_recent_messages(
            new_session_id, limit=5
        )
        for m in reversed(recent):
            if m.role == "user":
                user_msg_content = m.content
                break

        if not user_msg_content:
            user_msg_content = "继续"

        new_request = ChatRequest(
            character_id=msg.character_id,
            message=user_msg_content,
            model_tier=model_tier or ModelTier.SPEED,
            session_id=new_session_id,
            scene_id=msg.scene_id,
        )

        async for event in self.stream_chat(session, user_id, new_request):
            yield event

    async def set_message_feedback(
        self,
        session: AsyncSession,
        user_id: str,
        message_id: str,
        feedback: str,
    ) -> None:
        """设置消息反馈（like/dislike）。"""
        msg = await self._memory_repo.get_message_by_id(message_id, user_id)
        if not msg:
            raise MessageNotFoundError(message_id)
        if msg.role != "assistant":
            raise MessageFeedbackNotAllowedError()
        await self._memory_repo.update_message_feedback(message_id, feedback)
        await session.commit()

    async def toggle_message_pin(
        self,
        session: AsyncSession,
        user_id: str,
        message_id: str,
        is_pinned: bool,
    ) -> None:
        """切换消息固定状态。"""
        msg = await self._memory_repo.get_message_by_id(message_id, user_id)
        if not msg:
            raise MessageNotFoundError(message_id)
        await self._memory_repo.toggle_message_pin(message_id, is_pinned)
        await session.commit()

    def _build_user_message(self, request: ChatRequest) -> str:
        """构建用户消息（含指令）。"""
        message = request.message

        if request.directives:
            directive_text = ""
            for d in request.directives:
                directive_text += f"\n[{d.mode}] {d.instruction}"
            message = f"{message}\n{directive_text}"

        return message
