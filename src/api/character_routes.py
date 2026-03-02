"""角色 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db_session
from src.core.exceptions import YaiBaseError
from src.core.models import User
from src.core.prompt_builder import CharacterPromptBuilder
from src.core.schemas import (
    CharacterCreateRequest,
    CharacterResponse,
    CharacterUpdateRequest,
    PaginatedResponse,
)
from src.repositories.character_repo import CharacterRepository
from src.services.character_service import CharacterService

router = APIRouter()


def get_character_service(
    session: AsyncSession = Depends(get_db_session),
) -> CharacterService:
    """获取角色服务实例。"""
    character_repo = CharacterRepository(session)
    prompt_builder = CharacterPromptBuilder()
    return CharacterService(character_repo, prompt_builder)


def map_exception_to_http(exc: YaiBaseError) -> HTTPException:
    """将业务异常映射为 HTTP 异常。"""
    status_map = {
        "CHAR_NOT_FOUND": 404,
        "CHAR_PERMISSION_DENIED": 403,
        "CHAR_DEFINITION_INVALID": 400,
        "CHAR_CREATION_FORBIDDEN": 403,
    }
    status_code = status_map.get(exc.code, 400)
    return HTTPException(status_code=status_code, detail=exc.message)


@router.post("/", response_model=CharacterResponse, status_code=201)
async def create_character(
    request: CharacterCreateRequest,
    current_user: User = Depends(get_current_user),
    service: CharacterService = Depends(get_character_service),
) -> CharacterResponse:
    """创建角色。"""
    try:
        return await service.create_character(
            creator_id=current_user.id,
            can_create=current_user.can_create_character,
            request=request,
        )
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: str,
    current_user: User = Depends(get_current_user),
    service: CharacterService = Depends(get_character_service),
) -> CharacterResponse:
    """获取角色详情。"""
    try:
        return await service.get_character(
            character_id=character_id,
            user_id=current_user.id,
            is_admin=current_user.is_admin,
        )
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e


@router.get("/me/list", response_model=PaginatedResponse)
async def list_my_characters(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: CharacterService = Depends(get_character_service),
) -> PaginatedResponse:
    """我的角色列表。"""
    return await service.list_my_characters(
        user_id=current_user.id, page=page, size=size
    )


@router.get("/public/list", response_model=PaginatedResponse)
async def list_public_characters(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("popular", pattern="^(popular|newest)$"),
    service: CharacterService = Depends(get_character_service),
) -> PaginatedResponse:
    """公开角色列表。"""
    return await service.list_public_characters(page=page, size=size, sort=sort)


@router.get("/search", response_model=PaginatedResponse)
async def search_characters(
    q: str = Query(..., min_length=1),
    tag: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: CharacterService = Depends(get_character_service),
) -> PaginatedResponse:
    """搜索公开角色。"""
    return await service.search_characters(query=q, page=page, size=size, tag=tag)


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    request: CharacterUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: CharacterService = Depends(get_character_service),
) -> CharacterResponse:
    """更新角色。"""
    try:
        return await service.update_character(
            character_id=character_id,
            user_id=current_user.id,
            is_admin=current_user.is_admin,
            request=request,
        )
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e


@router.delete("/{character_id}", status_code=204)
async def delete_character(
    character_id: str,
    current_user: User = Depends(get_current_user),
    service: CharacterService = Depends(get_character_service),
) -> None:
    """删除角色。"""
    try:
        await service.delete_character(
            character_id=character_id,
            user_id=current_user.id,
            is_admin=current_user.is_admin,
        )
    except YaiBaseError as e:
        raise map_exception_to_http(e) from e
