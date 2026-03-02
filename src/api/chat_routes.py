"""对话相关 API 路由。"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db_session
from src.core.models import User
from src.core.schemas import (
    ChatHistoryPageResponse,
    ChatRequest,
    MessageEditRequest,
    MessageFeedbackRequest,
    MessageForkRequest,
    MessageRegenerateRequest,
    MessageResponse,
    ModelTier,
    SessionResponse,
    StorySummaryResponse,
    UserCustomizationRequest,
    UserCustomizationResponse,
)
from src.repositories.memory_repo import MemoryRepository
from src.repositories.story_summary_repo import StorySummaryRepository

router = APIRouter()


# ============================================================================
# SSE 流式对话
# ============================================================================


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    流式对话（SSE）。

    发送消息给 AI 角色，通过 Server-Sent Events 接收流式回复。

    SSE 事件格式：
    - {"type": "token", "content": "..."} — 流式 speech 输出
    - {"type": "action", "content": "..."} — 动作描述
    - {"type": "done", ...} — 流式完成（含完整结构化数据）
    - {"type": "error", ...} — 错误事件
    """
    from src.api.chat_deps import get_chat_service

    chat_service = await get_chat_service(session)

    async def event_generator():
        try:
            async for chunk in chat_service.stream_chat(
                session, user.id, request
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# 对话历史
# ============================================================================


@router.get("/history/{character_id}")
async def get_chat_history(
    character_id: str = Path(...),
    session_id: str = Query(...),
    before_message_id: str | None = Query(None),
    limit_rounds: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    获取对话历史分页。

    默认首屏加载最近 20 轮，上滑加载更多。
    """
    memory_repo = MemoryRepository(session)
    # 每轮 2 条消息（user + assistant）
    limit = limit_rounds * 2

    messages = await memory_repo.get_session_history(
        session_id=session_id,
        before_message_id=before_message_id,
        limit=limit + 1,
    )

    has_more = len(messages) > limit
    items = messages[:limit]

    next_before_id = items[-1].id if items and has_more else None

    return ChatHistoryPageResponse(
        session_id=session_id,
        items=[MessageResponse.model_validate(m) for m in reversed(items)],
        has_more=has_more,
        next_before_message_id=next_before_id,
    )


# ============================================================================
# 会话管理
# ============================================================================


@router.get("/sessions/{character_id}")
async def get_sessions(
    character_id: str = Path(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """获取与某角色的会话列表。"""
    memory_repo = MemoryRepository(session)
    offset = (page - 1) * size
    sessions = await memory_repo.get_user_sessions(
        user.id, character_id, offset, size
    )
    return sessions


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str = Path(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """删除会话（软删除所有消息）。"""
    memory_repo = MemoryRepository(session)
    await memory_repo.delete_session(session_id, user.id)
    await session.commit()
    return {"message": "会话已删除"}


@router.get("/summaries/{session_id}")
async def get_summaries(
    session_id: str = Path(...),
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """获取会话故事梗概。"""
    summary_repo = StorySummaryRepository(session)
    summaries = await summary_repo.get_by_session(session_id, limit)
    return [StorySummaryResponse.model_validate(s) for s in summaries]


@router.get("/recent-characters")
async def get_recent_characters(
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """获取最近对话角色列表（左侧导航用）。"""
    memory_repo = MemoryRepository(session)
    return await memory_repo.get_recent_character_sessions(user.id, limit)


# ============================================================================
# 消息操作
# ============================================================================


@router.put("/messages/{message_id}/edit")
async def edit_message(
    message_id: str = Path(...),
    request: MessageEditRequest = ...,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """编辑用户消息并重新生成 AI 回复（扣积分）。"""
    from src.api.chat_deps import get_chat_service

    chat_service = await get_chat_service(session)

    async def event_generator():
        async for chunk in chat_service.edit_message(
            session, user.id, message_id, request
        ):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/messages/{message_id}/regenerate")
async def regenerate_message(
    message_id: str = Path(...),
    request: MessageRegenerateRequest = ...,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """重新生成 AI 回复（扣积分）。"""
    from src.api.chat_deps import get_chat_service

    chat_service = await get_chat_service(session)

    async def event_generator():
        async for chunk in chat_service.regenerate_message(
            session, user.id, message_id, request
        ):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str = Path(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """删除单条消息。"""
    from src.api.chat_deps import get_chat_service

    chat_service = await get_chat_service(session)
    await chat_service.delete_message(session, user.id, message_id)
    return {"message": "消息已删除"}


@router.post("/messages/{message_id}/rewind")
async def rewind_to_message(
    message_id: str = Path(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """倒带到某条消息（不扣积分）。"""
    from src.api.chat_deps import get_chat_service

    chat_service = await get_chat_service(session)
    count = await chat_service.rewind_to_message(
        session, user.id, message_id
    )
    return {"message": f"已倒带，删除 {count} 条消息", "deleted_count": count}


@router.post("/messages/{message_id}/fork")
async def fork_from_message(
    message_id: str = Path(...),
    request: MessageForkRequest = ...,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """从某条消息处分叉新会话（扣积分）。"""
    from src.api.chat_deps import get_chat_service

    chat_service = await get_chat_service(session)

    async def event_generator():
        async for chunk in chat_service.fork_from_message(
            session, user.id, message_id, request.model_tier
        ):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.put("/messages/{message_id}/feedback")
async def set_message_feedback(
    message_id: str = Path(...),
    request: MessageFeedbackRequest = ...,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """消息点赞/点踩。"""
    from src.api.chat_deps import get_chat_service

    chat_service = await get_chat_service(session)
    await chat_service.set_message_feedback(
        session, user.id, message_id, request.feedback
    )
    return {"message": "反馈已记录"}


@router.put("/messages/{message_id}/pin")
async def toggle_message_pin(
    message_id: str = Path(...),
    is_pinned: bool = Query(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """固定/取消固定消息。"""
    from src.api.chat_deps import get_chat_service

    chat_service = await get_chat_service(session)
    await chat_service.toggle_message_pin(
        session, user.id, message_id, is_pinned
    )
    return {"message": "固定状态已更新"}


# ============================================================================
# 用户自定义设置
# ============================================================================


@router.get("/customization/{character_id}")
async def get_customization(
    character_id: str = Path(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """获取用户对某角色的自定义设置。"""
    from sqlalchemy import select
    from src.core.models import UserCharacterCustomization

    stmt = select(UserCharacterCustomization).where(
        UserCharacterCustomization.user_id == user.id,
        UserCharacterCustomization.character_id == character_id,
    )
    result = await session.execute(stmt)
    custom = result.scalar_one_or_none()

    if not custom:
        return {"character_id": character_id, "custom_prompt": None}

    return UserCustomizationResponse.model_validate(custom)


@router.put("/customization/{character_id}")
async def update_customization(
    character_id: str = Path(...),
    request: UserCustomizationRequest = ...,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """更新用户对某角色的自定义设置。"""
    from sqlalchemy import select
    from src.core.models import UserCharacterCustomization
    from src.utils.id_generator import generate_cuid

    stmt = select(UserCharacterCustomization).where(
        UserCharacterCustomization.user_id == user.id,
        UserCharacterCustomization.character_id == character_id,
    )
    result = await session.execute(stmt)
    custom = result.scalar_one_or_none()

    if custom:
        custom.custom_prompt = request.custom_prompt
    else:
        custom = UserCharacterCustomization(
            id=generate_cuid(),
            user_id=user.id,
            character_id=character_id,
            custom_prompt=request.custom_prompt,
        )
        session.add(custom)

    await session.commit()
    return {"message": "自定义设置已更新"}
