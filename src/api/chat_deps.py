"""对话服务依赖注入工厂。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.credit_engine import CreditEngine
from src.core.embedding_provider import GeminiEmbeddingProvider
from src.core.gemini_provider import GeminiProvider
from src.core.memory_engine import MemoryContextBuilder
from src.core.prompt_builder import CharacterPromptBuilder, ScenePromptBuilder
from src.core.story_summary_engine import StorySummaryEngine
from src.core.yaml_parser import YamlResponseParser
from src.repositories.memory_repo import MemoryRepository
from src.repositories.story_summary_repo import StorySummaryRepository
from src.repositories.user_repo import UserRepository
from src.repositories.transaction_repo import TransactionRepository
from src.services.character_service import CharacterService
from src.services.chat_service import ChatService
from src.services.credit_service import CreditService
from src.services.memory_service import MemoryService
from src.services.scene_service import SceneService
from src.services.story_summary_service import StorySummaryService


async def get_chat_service(session: AsyncSession) -> ChatService:
    """
    构建完整的 ChatService 依赖链。

    将所有依赖注入组装到一起。
    """
    settings = get_settings()

    # --- Providers ---
    model_provider = GeminiProvider(
        api_key=settings.gemini_api_key,
        speed_model=settings.gemini_speed_model,
        pro_model=settings.gemini_pro_model,
        elite_model=settings.gemini_elite_model,
        timeout=settings.gemini_request_timeout,
    )

    embedding_provider = GeminiEmbeddingProvider(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_embedding_model,
    )

    # --- Repositories ---
    memory_repo = MemoryRepository(session)
    summary_repo = StorySummaryRepository(session)
    user_repo = UserRepository(session)
    transaction_repo = TransactionRepository(session)

    # --- Engines ---
    credit_engine = CreditEngine(
        speed_price=settings.speed_credits_per_1k_tokens,
        pro_price=settings.pro_credits_per_1k_tokens,
        elite_price=settings.elite_credits_per_1k_tokens,
        hold_multiplier=settings.credit_hold_multiplier,
        hold_default_tokens=settings.credit_hold_default_tokens,
    )

    prompt_builder = CharacterPromptBuilder()
    scene_prompt_builder = ScenePromptBuilder(prompt_builder)

    context_builder = MemoryContextBuilder(
        prompt_builder=prompt_builder,
        scene_prompt_builder=scene_prompt_builder,
        max_short_term=settings.max_short_term_messages,
        max_long_term=settings.max_long_term_fragments,
        max_summaries=settings.max_story_summaries,
    )

    summary_engine = StorySummaryEngine(
        trigger_interval=settings.summary_trigger_interval,
        max_key_dialogues=settings.summary_max_key_dialogues,
        summary_max_length=settings.summary_max_length,
    )

    # --- Services ---
    from src.repositories.character_repo import CharacterRepository
    from src.repositories.scene_repo import SceneRepository

    character_service = CharacterService(
        character_repo=CharacterRepository(session),
    )

    scene_service = SceneService(
        scene_repo=SceneRepository(session),
    )

    credit_service = CreditService(
        engine=credit_engine,
        user_repo=user_repo,
        transaction_repo=transaction_repo,
    )

    memory_service = MemoryService(
        memory_repo=memory_repo,
        summary_repo=summary_repo,
        context_builder=context_builder,
        embedding_provider=embedding_provider,
        max_short_term=settings.max_short_term_messages,
        max_long_term=settings.max_long_term_fragments,
        max_summaries=settings.max_story_summaries,
    )

    story_summary_service = StorySummaryService(
        summary_engine=summary_engine,
        summary_repo=summary_repo,
        memory_repo=memory_repo,
        model_provider=model_provider,
        embedding_provider=embedding_provider,
        summary_model_tier=settings.summary_model_tier,
    )

    yaml_parser = YamlResponseParser()

    return ChatService(
        character_service=character_service,
        scene_service=scene_service,
        memory_service=memory_service,
        credit_service=credit_service,
        model_provider=model_provider,
        yaml_parser=yaml_parser,
        story_summary_service=story_summary_service,
        memory_repo=memory_repo,
    )
