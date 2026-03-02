"""积分相关 API 路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_admin, get_current_user, get_db_session
from src.core.credit_engine import CreditEngine
from src.core.models import User
from src.core.schemas import (
    AdminCreditAdjustRequest,
    CreditBalanceResponse,
    PaginatedResponse,
    TransactionResponse,
)
from src.repositories.transaction_repo import TransactionRepository
from src.repositories.user_repo import UserRepository
from src.services.credit_service import CreditService
from src.config import get_settings

router = APIRouter()


def get_credit_engine() -> CreditEngine:
    """获取积分引擎（单例）。"""
    settings = get_settings()
    return CreditEngine(
        speed_price=settings.speed_credits_per_1k_tokens,
        pro_price=settings.pro_credits_per_1k_tokens,
        elite_price=settings.elite_credits_per_1k_tokens,
        hold_multiplier=settings.credit_hold_multiplier,
        hold_default_tokens=settings.credit_hold_default_tokens,
    )


def get_credit_service(
    session: AsyncSession = Depends(get_db_session),
    engine: CreditEngine = Depends(get_credit_engine),
) -> CreditService:
    """获取积分服务。"""
    user_repo = UserRepository(session)
    transaction_repo = TransactionRepository(session)
    return CreditService(engine, user_repo, transaction_repo)


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    current_user: User = Depends(get_current_user),
    service: CreditService = Depends(get_credit_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    查询当前用户的积分余额。

    返回:
    - credits: 当前积分余额
    - tier_pricing: 各档位定价（speed/pro/elite）
    """
    balance = await service.get_balance(session, current_user.id)
    tier_pricing = service.engine.get_all_pricing()

    return CreditBalanceResponse(credits=balance, tier_pricing=tier_pricing)


@router.get("/transactions", response_model=PaginatedResponse[TransactionResponse])
async def get_transactions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """
    查询当前用户的积分流水记录（按时间倒序）。

    参数:
    - page: 页码（从 1 开始）
    - size: 每页数量（默认 20，最大 100）
    """
    transaction_repo = TransactionRepository(session)

    offset = (page - 1) * size
    items = await transaction_repo.get_by_user(current_user.id, offset, size)
    total = await transaction_repo.count_by_user(current_user.id)

    return PaginatedResponse(
        items=[TransactionResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/pricing")
async def get_pricing(engine: CreditEngine = Depends(get_credit_engine)):
    """
    获取各档位定价信息。

    返回:
    - speed: Speed 档位每 1k tokens 积分消耗
    - pro: Pro 档位每 1k tokens 积分消耗
    - elite: Elite 档位每 1k tokens 积分消耗
    """
    return engine.get_all_pricing()


@router.post("/admin/adjust", dependencies=[Depends(get_current_admin)])
async def admin_adjust_credits(
    request: AdminCreditAdjustRequest,
    session: AsyncSession = Depends(get_db_session),
    service: CreditService = Depends(get_credit_service),
    admin: User = Depends(get_current_admin),
):
    """
    管理员调整用户积分（需要管理员权限）。

    参数:
    - user_id: 目标用户 ID
    - amount: 调整量（正数为增加，负数为扣减）
    - reason: 调整原因

    异常:
    - 403: 非管理员用户
    - 404: 用户不存在
    - 400: 调整后余额为负
    """
    await service.admin_adjust(
        session=session,
        user_id=request.user_id,
        amount=request.amount,
        reason=request.reason,
        operator_id=admin.id,
    )
    await session.commit()

    return {"message": "积分调整成功"}
