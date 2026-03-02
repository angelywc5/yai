"""积分业务服务 — 事务编排与流程控制。"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.credit_engine import CreditEngine, CreditHold, CreditSettlement
from src.core.exceptions import (
    CreditTransactionError,
    InsufficientCreditsError,
    ResourceNotFoundError,
)
from src.core.models import User
from src.core.schemas import ModelTier
from src.repositories.transaction_repo import TransactionRepository
from src.repositories.user_repo import UserRepository
from src.utils.id_generator import generate_cuid

logger = logging.getLogger(__name__)


class CreditService:
    """
    积分业务服务。

    职责:
    - 预扣积分（行级锁保证并发安全）
    - 结算积分（计算实际消耗并退还差额）
    - 回滚预扣（AI 调用失败时全额退款）
    - 管理员调整积分
    """

    def __init__(
        self,
        engine: CreditEngine,
        user_repo: UserRepository,
        transaction_repo: TransactionRepository,
    ):
        """初始化积分服务。"""
        self.engine = engine
        self.user_repo = user_repo
        self.transaction_repo = transaction_repo

    async def hold_credits(
        self, session: AsyncSession, user_id: str, tier: ModelTier
    ) -> CreditHold:
        """
        预扣积分（在事务内执行）。

        流程:
        1. SELECT ... FOR UPDATE 锁定积分行
        2. 计算预扣金额
        3. 校验余额
        4. 扣减预估金额
        5. 写入流水

        Args:
            session: 数据库会话（事务由调用方管理）
            user_id: 用户 ID
            tier: 模型档位

        Returns:
            预扣凭证

        Raises:
            ResourceNotFoundError: 用户不存在
            InsufficientCreditsError: 积分不足
        """
        # 1. 行级锁：SELECT ... FOR UPDATE
        stmt = select(User.credits).where(User.id == user_id).with_for_update()
        result = await session.execute(stmt)
        current_balance = result.scalar()

        if current_balance is None:
            raise ResourceNotFoundError("User", user_id)

        # 2. 计算预扣金额
        estimated_amount = self.engine.estimate_hold_amount(tier)

        # 3. 校验余额
        if not self.engine.validate_balance(current_balance, estimated_amount):
            raise InsufficientCreditsError(
                required=estimated_amount, available=current_balance
            )

        # 4. 扣减预估金额
        await self.user_repo.update_credits(user_id, -estimated_amount)

        # 5. 写入流水
        await self.transaction_repo.create(
            user_id=user_id,
            amount=-estimated_amount,
            reason=f"Credit Hold - {tier.value}",
        )

        hold_id = generate_cuid()
        logger.info(
            f"Credit hold: user={user_id}, tier={tier.value}, "
            f"amount={estimated_amount}, hold_id={hold_id}"
        )

        return CreditHold(
            hold_id=hold_id,
            user_id=user_id,
            tier=tier,
            estimated_amount=estimated_amount,
        )

    async def settle_credits(
        self, session: AsyncSession, hold: CreditHold, actual_tokens: int
    ) -> CreditSettlement:
        """
        结算积分（在新事务内执行）。

        流程:
        1. 计算实际消耗
        2. 计算退还差额
        3. 退还多扣积分
        4. 写入结算流水

        Args:
            session: 数据库会话（新事务）
            hold: 预扣凭证
            actual_tokens: 实际消耗的 token 数量

        Returns:
            结算结果
        """
        # 1. 计算实际消耗
        actual_amount = self.engine.calculate_actual_cost(hold.tier, actual_tokens)

        # 2. 计算退还差额
        refund = self.engine.calculate_refund(hold.estimated_amount, actual_amount)

        # 3. 退还多扣积分（如果有）
        if refund > 0:
            await self.user_repo.update_credits(hold.user_id, refund)
            await self.transaction_repo.create(
                user_id=hold.user_id,
                amount=refund,
                reason=f"Credit Settlement Refund - {hold.tier.value}",
            )

        logger.info(
            f"Credit settle: user={hold.user_id}, tier={hold.tier.value}, "
            f"estimated={hold.estimated_amount}, actual={actual_amount}, "
            f"refund={refund}, tokens={actual_tokens}"
        )

        return CreditSettlement(
            hold=hold,
            actual_tokens_used=actual_tokens,
            actual_amount=actual_amount,
            refund=refund,
        )

    async def rollback_hold(self, session: AsyncSession, hold: CreditHold) -> None:
        """
        回滚预扣（AI 调用失败时全额退款）。

        Args:
            session: 数据库会话
            hold: 预扣凭证
        """
        await self.user_repo.update_credits(hold.user_id, hold.estimated_amount)
        await self.transaction_repo.create(
            user_id=hold.user_id,
            amount=hold.estimated_amount,
            reason=f"Credit Rollback - AI Error - {hold.tier.value}",
        )

        logger.warning(
            f"Credit rollback: user={hold.user_id}, tier={hold.tier.value}, "
            f"amount={hold.estimated_amount}"
        )

    async def get_balance(self, session: AsyncSession, user_id: str) -> int:
        """
        查询用户积分余额。

        Args:
            session: 数据库会话
            user_id: 用户 ID

        Returns:
            当前积分余额

        Raises:
            ResourceNotFoundError: 用户不存在
        """
        user = await self.user_repo.get_by_id(session, user_id)
        if not user:
            raise ResourceNotFoundError("User", user_id)
        return user.credits

    async def admin_adjust(
        self,
        session: AsyncSession,
        user_id: str,
        amount: int,
        reason: str,
        operator_id: str,
    ) -> None:
        """
        管理员手动调整积分。

        Args:
            session: 数据库会话（事务由调用方管理）
            user_id: 用户 ID
            amount: 调整量（正数为增加，负数为扣减）
            reason: 调整原因
            operator_id: 管理员 ID

        Raises:
            ResourceNotFoundError: 用户不存在
            CreditTransactionError: 调整后余额为负
        """
        # 检查用户是否存在
        user = await self.user_repo.get_by_id(session, user_id)
        if not user:
            raise ResourceNotFoundError("User", user_id)

        # 如果是扣减，校验余额
        if amount < 0 and user.credits + amount < 0:
            raise CreditTransactionError(
                f"调整后余额为负: 当前 {user.credits}, 调整 {amount}"
            )

        # 更新积分
        await self.user_repo.update_credits(user_id, amount)

        # 写入流水
        await self.transaction_repo.create(
            user_id=user_id,
            amount=amount,
            reason=f"Admin Adjust - {reason}",
            operator_id=operator_id,
        )

        logger.info(
            f"Admin adjust: user={user_id}, amount={amount}, "
            f"operator={operator_id}, reason={reason}"
        )
