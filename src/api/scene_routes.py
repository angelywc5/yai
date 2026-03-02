"""场景 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db_session
from src.core.exceptions import YaiBaseError
from src.core.models import User
from src.core.prompt_builder import CharacterPromptBuilder, ScenePromptBuilder
from src.core.schemas import (
    PaginatedResponse,
    SceneCharacterRequest,
    SceneCreateRequest,
    SceneResponse,
    SceneUpdateRequest,
)
from src.repositories.character_repo import CharacterRepository
from src.repositories.scene_repo import SceneRepository
from src.services.scene_service import SceneService

router = APIRouter()


def get_scene_service(
    session: AsyncSession = Depends(get_db_session),
) -> SceneService:
    """获取场景服务实例。"""
    scene_repo = SceneRepository(session)
    character_repo = CharacterRepository(session)
    char_builder = CharacterPromptBuilder()
    scene_builder = ScenePromptBuilder(char_builder)
    return SceneService(
        scene_repo, character_repo, scene_builder, max_scene_characters=10
    )


def map_exception_to_http(exc: YaiBaseError) -> HTTPException:
    """将业务异常映射为 HTTP 异常。"""
    status_map = {
        "SCENE_NOT_FOUND": 404,
        "SCENE_PERMISSION_DENIED": 403,
        "SCENE_CREATION_FORBIDDEN": 403,
        "SCENE_CHARACTER_LIMIT": 400,
        "SCENE_CHARACTER_NOT_ACCESSIBLE": 403,
        "CHAR_NOT_FOUND": 404,
    }
    status_code = status_map.get(exc.code, 400)
    return HTTPException(status_code=status_code, detail=exc.message)


@router.post("/", response_model=SceneResponse, status_code=201)
async def create_scene(
    request: SceneCreateRequest,
    current_user: User = Depends(get_current_user),
    service: SceneService = Depends(get_scene_service),
) -> SceneResponse:
    """创建场景。"""
    try:
        return await service.create_scene(
            creator_id=current_user.id,
            can_create=current_user.can_create_scene,
            request=request,
        )
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e


@router.get("/{scene_id}", response_model=SceneResponse)
async def get_scene(
    scene_id: str,
    current_user: User = Depends(get_current_user),
    service: SceneService = Depends(get_scene_service),
) -> SceneResponse:
    """获取场景详情。"""
    try:
        return await service.get_scene(
            scene_id=scene_id,
            user_id=current_user.id,
            is_admin=current_user.is_admin,
        )
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e


@router.get("/me/list", response_model=PaginatedResponse)
async def list_my_scenes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: SceneService = Depends(get_scene_service),
) -> PaginatedResponse:
    """我的场景列表。"""
    return await service.list_my_scenes(user_id=current_user.id, page=page, size=size)


@router.get("/public/list", response_model=PaginatedResponse)
async def list_public_scenes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("popular", pattern="^(popular|newest)$"),
    service: SceneService = Depends(get_scene_service),
) -> PaginatedResponse:
    """公开场景列表。"""
    return await service.list_public_scenes(page=page, size=size, sort=sort)


@router.get("/search", response_model=PaginatedResponse)
async def search_scenes(
    q: str = Query(..., min_length=1),
    tag: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: SceneService = Depends(get_scene_service),
) -> PaginatedResponse:
    """搜索公开场景。"""
    return await service.search_scenes(query=q, page=page, size=size, tag=tag)


@router.put("/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: str,
    request: SceneUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: SceneService = Depends(get_scene_service),
) -> SceneResponse:
    """更新场景。"""
    try:
        return await service.update_scene(
            scene_id=scene_id,
            user_id=current_user.id,
            is_admin=current_user.is_admin,
            request=request,
        )
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e


@router.delete("/{scene_id}", status_code=204)
async def delete_scene(
    scene_id: str,
    current_user: User = Depends(get_current_user),
    service: SceneService = Depends(get_scene_service),
) -> None:
    """删除场景。"""
    try:
        await service.delete_scene(
            scene_id=scene_id,
            user_id=current_user.id,
            is_admin=current_user.is_admin,
        )
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e


@router.post("/{scene_id}/characters", status_code=201)
async def add_character_to_scene(
    scene_id: str,
    request: SceneCharacterRequest,
    current_user: User = Depends(get_current_user),
    service: SceneService = Depends(get_scene_service),
) -> dict[str, str]:
    """向场景添加角色。"""
    try:
        await service.add_character_to_scene(
            scene_id=scene_id, user_id=current_user.id, request=request
        )
        return {"message": "角色已添加到场景"}
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e


@router.delete("/{scene_id}/characters/{character_id}", status_code=204)
async def remove_character_from_scene(
    scene_id: str,
    character_id: str,
    current_user: User = Depends(get_current_user),
    service: SceneService = Depends(get_scene_service),
) -> None:
    """从场景移除角色。"""
    try:
        await service.remove_character_from_scene(
            scene_id=scene_id, user_id=current_user.id, character_id=character_id
        )
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e
