"""积分流水数据访问层。"""

from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Transaction


class TransactionRepository:
    """积分流水数据访问。"""

    def __init__(self, session: AsyncSession):
        """初始化 Repository。"""
        self.session = session

    async def create(
        self,
        user_id: str,
        amount: int,
        reason: str,
        operator_id: str | None = None,
    ) -> Transaction:
        """
        创建积分流水记录。

        Args:
            user_id: 用户 ID
            amount: 积分变动量（正数为增加，负数为扣减）
            reason: 变动原因
            operator_id: 操作者 ID（管理员调整时使用）

        Returns:
            创建的流水记录
        """
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            reason=reason,
            operator_id=operator_id,
        )
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def get_by_user(
        self, user_id: str, offset: int = 0, limit: int = 20
    ) -> list[Transaction]:
        """
        查询用户的积分流水（按时间倒序）。

        Args:
            user_id: 用户 ID
            offset: 偏移量
            limit: 每页数量

        Returns:
            流水记录列表
        """
        stmt = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_and_time_range(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Transaction]:
        """
        查询用户在指定时间范围内的积分流水。

        Args:
            user_id: 用户 ID
            start: 开始时间（包含）
            end: 结束时间（包含）
            offset: 偏移量
            limit: 每页数量

        Returns:
            流水记录列表
        """
        stmt = (
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.created_at >= start,
                Transaction.created_at <= end,
            )
            .order_by(desc(Transaction.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: str) -> int:
        """
        统计用户的流水记录总数。

        Args:
            user_id: 用户 ID

        Returns:
            记录总数
        """
        stmt = select(func.count()).where(Transaction.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def sum_by_user_and_time_range(
        self, user_id: str, start: datetime, end: datetime
    ) -> dict[str, int]:
        """
        统计用户在指定时间范围内的积分消耗和退款。

        Args:
            user_id: 用户 ID
            start: 开始时间
            end: 结束时间

        Returns:
            {"consumed": 消耗总额, "refunded": 退款总额, "net": 净消耗}
        """
        stmt = select(
            func.sum(
                func.case((Transaction.amount < 0, -Transaction.amount), else_=0)
            ).label("consumed"),
            func.sum(
                func.case((Transaction.amount > 0, Transaction.amount), else_=0)
            ).label("refunded"),
        ).where(
            Transaction.user_id == user_id,
            Transaction.created_at >= start,
            Transaction.created_at <= end,
        )
        result = await self.session.execute(stmt)
        row = result.one()
        consumed = row.consumed or 0
        refunded = row.refunded or 0
        return {
            "consumed": consumed,
            "refunded": refunded,
            "net": consumed - refunded,
        }
