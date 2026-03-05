"""角色业务服务。"""

from __future__ import annotations

from src.core.exceptions import (
    CharacterCreationForbiddenError,
    CharacterNotFoundError,
    CharacterPermissionError,
)
from src.core.prompt_builder import CharacterPromptBuilder
from src.core.schemas import (
    CharacterCreateRequest,
    CharacterPublicResponse,
    CharacterResponse,
    CharacterUpdateRequest,
    PaginatedResponse,
)
from src.repositories.character_repo import CharacterRepository


class CharacterService:
    """角色业务编排。"""

    def __init__(
        self,
        character_repo: CharacterRepository,
        prompt_builder: CharacterPromptBuilder,
    ):
        self._repo = character_repo
        self._prompt_builder = prompt_builder

    async def create_character(
        self, creator_id: str, can_create: bool, request: CharacterCreateRequest
    ) -> CharacterResponse:
        """创建角色（校验 can_create_character 权限）。"""
        if not can_create:
            raise CharacterCreationForbiddenError()

        # request.definition 已由 Pydantic 自动校验为 CharacterDefinition
        # 转为 dict 存入数据库
        definition_dict = request.definition.model_dump()

        # 创建角色
        character = await self._repo.create(
            name=request.name,
            definition=definition_dict,
            creator_id=creator_id,
            avatar_url=request.avatar_url,
            avatar_source=request.avatar_source or "default",
            tagline=request.tagline or "",
            tags=request.tags or [],
            is_public=request.is_public,
        )

        return CharacterResponse.model_validate(character)

    async def get_character(
        self, character_id: str, user_id: str, is_admin: bool = False
    ) -> CharacterResponse | CharacterPublicResponse:
        """
        获取角色详情：
        - 创建者/管理员：返回 CharacterResponse（含完整 definition）
        - 非创建者：返回 CharacterPublicResponse（仅暴露 personality 列表）
        """
        character = await self._repo.get_by_id_active(character_id)
        if not character:
            raise CharacterNotFoundError(character_id)

        # 创建者或管理员可以看完整信息
        if character.creator_id == user_id or is_admin:
            return CharacterResponse.model_validate(character)

        # 非创建者只能看精简版
        return CharacterPublicResponse(
            id=character.id,
            name=character.name,
            avatar_url=character.avatar_url,
            avatar_source=character.avatar_source,
            tagline=character.tagline,
            personality_summary=character.definition.get("personality", []),
            tags=character.tags,
            is_public=character.is_public,
            chat_count=character.chat_count,
            like_count=character.like_count,
            creator_id=character.creator_id,
            creator_username=character.creator.username if character.creator else "",
            creator_display_name=character.creator.display_name if character.creator else "",
            created_at=character.created_at,
        )

    async def list_my_characters(
        self, user_id: str, page: int, size: int
    ) -> PaginatedResponse:
        """获取我的角色列表。"""
        offset = (page - 1) * size
        characters = await self._repo.get_by_creator(user_id, offset, size)
        total = await self._repo.count_by_creator(user_id)

        items = [CharacterResponse.model_validate(c) for c in characters]
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    async def list_public_characters(
        self, page: int, size: int, sort: str = "popular"
    ) -> PaginatedResponse:
        """
        列出公开角色，支持 sort 排序：
        - popular: 按 chat_count DESC（默认）
        - newest: 按 created_at DESC
        """
        offset = (page - 1) * size
        characters = await self._repo.get_public(offset, size, sort)
        total = await self._repo.count_public()

        items = [
            CharacterPublicResponse(
                id=c.id,
                name=c.name,
                avatar_url=c.avatar_url,
                avatar_source=c.avatar_source,
                tagline=c.tagline,
                personality_summary=c.definition.get("personality", []),
                tags=c.tags,
                is_public=c.is_public,
                chat_count=c.chat_count,
                like_count=c.like_count,
                creator_id=c.creator_id,
                creator_username=c.creator.username if c.creator else "",
                creator_display_name=c.creator.display_name if c.creator else "",
                created_at=c.created_at,
            )
            for c in characters
        ]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    async def search_characters(
        self, query: str, page: int, size: int, tag: str | None = None
    ) -> PaginatedResponse:
        """搜索公开角色，可按 tag 过滤。"""
        offset = (page - 1) * size
        characters = await self._repo.search(query, tag, offset, size)
        total = await self._repo.count_search(query, tag)

        items = [
            CharacterPublicResponse(
                id=c.id,
                name=c.name,
                avatar_url=c.avatar_url,
                avatar_source=c.avatar_source,
                tagline=c.tagline,
                personality_summary=c.definition.get("personality", []),
                tags=c.tags,
                is_public=c.is_public,
                chat_count=c.chat_count,
                like_count=c.like_count,
                creator_id=c.creator_id,
                creator_username=c.creator.username if c.creator else "",
                creator_display_name=c.creator.display_name if c.creator else "",
                created_at=c.created_at,
            )
            for c in characters
        ]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    async def update_character(
        self,
        character_id: str,
        user_id: str,
        is_admin: bool,
        request: CharacterUpdateRequest,
    ) -> CharacterResponse:
        """更新角色。"""
        character = await self._repo.get_by_id_active(character_id)
        if not character:
            raise CharacterNotFoundError(character_id)

        # 权限校验（仅创建者或管理员）
        if character.creator_id != user_id and not is_admin:
            raise CharacterPermissionError()

        # 构建更新参数
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.avatar_url is not None:
            update_data["avatar_url"] = request.avatar_url
            update_data["avatar_source"] = request.avatar_source or "upload"
        if request.tagline is not None:
            update_data["tagline"] = request.tagline
        if request.definition is not None:
            update_data["definition"] = request.definition.model_dump()
        if request.tags is not None:
            update_data["tags"] = request.tags
        if request.is_public is not None:
            update_data["is_public"] = request.is_public

        # 更新
        updated_character = await self._repo.update(character_id, **update_data)
        return CharacterResponse.model_validate(updated_character)

    async def delete_character(
        self, character_id: str, user_id: str, is_admin: bool
    ) -> None:
        """删除角色（软删除）。"""
        character = await self._repo.get_by_id_active(character_id)
        if not character:
            raise CharacterNotFoundError(character_id)

        # 权限校验（仅创建者或管理员）
        if character.creator_id != user_id and not is_admin:
            raise CharacterPermissionError()

        # 软删除
        await self._repo.soft_delete(character_id)

    async def increment_like_count(self, character_id: str) -> None:
        """增加角色点赞数（用户对 AI 回复点赞时联动）。"""
        await self._repo.increment_like_count(character_id)
