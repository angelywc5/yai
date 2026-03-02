"""场景业务服务。"""

from __future__ import annotations

from src.core.exceptions import (
    CharacterNotFoundError,
    SceneCharacterLimitError,
    SceneCharacterNotAccessibleError,
    SceneCreationForbiddenError,
    SceneNotFoundError,
    ScenePermissionError,
)
from src.core.prompt_builder import ScenePromptBuilder
from src.core.schemas import (
    PaginatedResponse,
    SceneCharacterRequest,
    SceneCreateRequest,
    SceneResponse,
    SceneUpdateRequest,
)
from src.repositories.character_repo import CharacterRepository
from src.repositories.scene_repo import SceneRepository


class SceneService:
    """场景业务编排。"""

    def __init__(
        self,
        scene_repo: SceneRepository,
        character_repo: CharacterRepository,
        scene_prompt_builder: ScenePromptBuilder,
        max_scene_characters: int = 10,
    ):
        self._scene_repo = scene_repo
        self._character_repo = character_repo
        self._prompt_builder = scene_prompt_builder
        self._max_scene_characters = max_scene_characters

    async def create_scene(
        self, creator_id: str, can_create: bool, request: SceneCreateRequest
    ) -> SceneResponse:
        """
        创建场景：
        1. 校验 can_create_scene 权限
        2. 校验各文本字段长度上限（genre/mood/time_period/setting_location max 100 字符）
        3. 校验 character_ids 中的角色是否可用（公开或自己创建的）
        4. 校验 character_ids 非空（场景必须绑定至少 1 个角色）
        5. 创建场景记录（含自由文本元数据）
        6. 批量关联角色
        """
        if not can_create:
            raise SceneCreationForbiddenError()

        # 校验 character_ids 非空
        if not request.character_ids:
            raise ValueError("场景必须绑定至少 1 个角色")

        # 校验角色可访问性
        for char_id in request.character_ids:
            char = await self._character_repo.get_by_id_active(char_id)
            if not char:
                raise CharacterNotFoundError(char_id)
            if not char.is_public and char.creator_id != creator_id:
                raise SceneCharacterNotAccessibleError(char_id)

        # 创建场景
        scene = await self._scene_repo.create(
            name=request.name,
            description=request.description,
            scene_definition=request.scene_definition,
            greeting=request.greeting,
            creator_id=creator_id,
            cover_image_url=request.cover_image_url,
            cover_source=request.cover_source or "default",
            allow_character_selection=request.allow_character_selection,
            is_public=request.is_public,
            genre=request.genre or "",
            time_period=request.time_period or "",
            setting_location=request.setting_location or "",
            mood=request.mood or "",
            player_objective=request.player_objective or "",
            tags=request.tags or [],
        )

        # 批量关联角色
        for idx, char_id in enumerate(request.character_ids):
            await self._scene_repo.add_character(
                scene_id=scene.id,
                character_id=char_id,
                role_in_scene=(
                    request.character_roles.get(char_id, "")
                    if request.character_roles
                    else ""
                ),
                sort_order=idx,
            )

        return SceneResponse.model_validate(scene)

    async def get_scene(
        self, scene_id: str, user_id: str, is_admin: bool = False
    ) -> SceneResponse:
        """获取场景详情。"""
        scene = await self._scene_repo.get_by_id_active(scene_id)
        if not scene:
            raise SceneNotFoundError(scene_id)

        return SceneResponse.model_validate(scene)

    async def list_my_scenes(
        self, user_id: str, page: int, size: int
    ) -> PaginatedResponse:
        """获取我的场景列表。"""
        offset = (page - 1) * size
        scenes = await self._scene_repo.get_by_creator(user_id, offset, size)
        total = await self._scene_repo.count_by_creator(user_id)

        items = [SceneResponse.model_validate(s) for s in scenes]
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    async def list_public_scenes(
        self, page: int, size: int, sort: str = "popular"
    ) -> PaginatedResponse:
        """
        列出公开场景，支持 sort 排序：
        - popular: 按 play_count DESC（默认）
        - newest: 按 created_at DESC
        """
        offset = (page - 1) * size
        scenes = await self._scene_repo.get_public(offset, size, sort)
        total = await self._scene_repo.count_public()

        items = [SceneResponse.model_validate(s) for s in scenes]
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    async def search_scenes(
        self, query: str, page: int, size: int, tag: str | None = None
    ) -> PaginatedResponse:
        """搜索公开场景。"""
        offset = (page - 1) * size
        scenes = await self._scene_repo.search(query, tag, offset, size)
        total = await self._scene_repo.count_search(query, tag)

        items = [SceneResponse.model_validate(s) for s in scenes]
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    async def update_scene(
        self,
        scene_id: str,
        user_id: str,
        is_admin: bool,
        request: SceneUpdateRequest,
    ) -> SceneResponse:
        """更新场景。"""
        scene = await self._scene_repo.get_by_id_active(scene_id)
        if not scene:
            raise SceneNotFoundError(scene_id)

        # 权限校验（仅创建者或管理员）
        if scene.creator_id != user_id and not is_admin:
            raise ScenePermissionError()

        # 构建更新参数
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.scene_definition is not None:
            update_data["scene_definition"] = request.scene_definition
        if request.greeting is not None:
            update_data["greeting"] = request.greeting
        if request.cover_image_url is not None:
            update_data["cover_image_url"] = request.cover_image_url
            update_data["cover_source"] = request.cover_source or "upload"
        if request.allow_character_selection is not None:
            update_data["allow_character_selection"] = request.allow_character_selection
        if request.is_public is not None:
            update_data["is_public"] = request.is_public
        if request.genre is not None:
            update_data["genre"] = request.genre
        if request.time_period is not None:
            update_data["time_period"] = request.time_period
        if request.setting_location is not None:
            update_data["setting_location"] = request.setting_location
        if request.mood is not None:
            update_data["mood"] = request.mood
        if request.player_objective is not None:
            update_data["player_objective"] = request.player_objective
        if request.tags is not None:
            update_data["tags"] = request.tags

        # 更新
        updated_scene = await self._scene_repo.update(scene_id, **update_data)
        return SceneResponse.model_validate(updated_scene)

    async def delete_scene(self, scene_id: str, user_id: str, is_admin: bool) -> None:
        """删除场景（软删除）。"""
        scene = await self._scene_repo.get_by_id_active(scene_id)
        if not scene:
            raise SceneNotFoundError(scene_id)

        # 权限校验（仅创建者或管理员）
        if scene.creator_id != user_id and not is_admin:
            raise ScenePermissionError()

        # 软删除
        await self._scene_repo.soft_delete(scene_id)

    async def add_character_to_scene(
        self, scene_id: str, user_id: str, request: SceneCharacterRequest
    ) -> None:
        """
        向场景添加角色：
        - 校验场景所有权
        - 校验角色可用性（公开或自己创建的）
        - 校验场景角色数量上限
        """
        scene = await self._scene_repo.get_by_id_active(scene_id)
        if not scene:
            raise SceneNotFoundError(scene_id)

        # 权限校验（仅创建者）
        if scene.creator_id != user_id:
            raise ScenePermissionError()

        # 校验角色数量上限
        char_count = await self._scene_repo.count_scene_characters(scene_id)
        if char_count >= self._max_scene_characters:
            raise SceneCharacterLimitError(self._max_scene_characters)

        # 校验角色可访问性
        char = await self._character_repo.get_by_id_active(request.character_id)
        if not char:
            raise CharacterNotFoundError(request.character_id)
        if not char.is_public and char.creator_id != user_id:
            raise SceneCharacterNotAccessibleError(request.character_id)

        # 添加角色
        await self._scene_repo.add_character(
            scene_id=scene_id,
            character_id=request.character_id,
            role_in_scene=request.role_in_scene or "",
            sort_order=char_count,
        )

    async def remove_character_from_scene(
        self, scene_id: str, user_id: str, character_id: str
    ) -> None:
        """从场景移除角色。"""
        scene = await self._scene_repo.get_by_id_active(scene_id)
        if not scene:
            raise SceneNotFoundError(scene_id)

        # 权限校验（仅创建者）
        if scene.creator_id != user_id:
            raise ScenePermissionError()

        # 移除角色
        await self._scene_repo.remove_character(scene_id, character_id)
