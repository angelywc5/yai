"""管理后台业务服务 — 用户管理部分。"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Character, Message, Scene, SceneCharacter, Transaction, User
from src.core.schemas import (
    AdminConsumptionDailyPoint,
    AdminUserConsumptionResponse,
    CharacterResponse,
    MessageResponse,
    ModelTier,
    PaginatedResponse,
    SceneResponse,
    TransactionResponse,
    UserDetailResponse,
    UserResponse,
)
from src.core.exceptions import ResourceNotFoundError, CreditTransactionError
from src.utils.redis_client import redis_manager

logger = logging.getLogger(__name__)

MODEL_SWITCHES_KEY = "yai:model_switches"


class AdminService:
    """
    管理后台业务服务。

    职责：用户管理、角色/场景管理、消耗查询、模型开关。
    """

    # ------------------------------------------------------------------
    # 用户管理
    # ------------------------------------------------------------------

    async def list_users(
        self,
        session: AsyncSession,
        search: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[UserResponse]:
        """搜索/分页用户列表。"""
        conditions = []
        if search:
            pattern = f"%{search}%"
            conditions.append(
                or_(
                    User.email.ilike(pattern),
                    User.username.ilike(pattern),
                    User.display_name.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(User)
        query_stmt = select(User).order_by(desc(User.created_at))

        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
            query_stmt = query_stmt.where(and_(*conditions))

        total = (await session.execute(count_stmt)).scalar() or 0
        offset = (page - 1) * size
        users = (
            await session.execute(query_stmt.offset(offset).limit(size))
        ).scalars().all()

        items = [
            UserResponse(
                id=u.id,
                email=u.email,
                username=u.username,
                display_name=u.display_name,
                email_verified=u.email_verified,
                credits=u.credits,
                is_admin=u.is_admin,
                avatar_url=u.avatar_url,
                created_at=u.created_at,
            )
            for u in users
        ]
        pages = max(1, (total + size - 1) // size)
        return PaginatedResponse[UserResponse](
            items=items, total=total, page=page, size=size, pages=pages
        )

    async def get_user_detail(
        self, session: AsyncSession, user_id: str
    ) -> UserDetailResponse:
        """获取用户详情（含角色/场景数量）。"""
        user = (
            await session.execute(select(User).where(User.id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise ResourceNotFoundError("User", user_id)

        char_count = (
            await session.execute(
                select(func.count())
                .select_from(Character)
                .where(Character.creator_id == user_id)
            )
        ).scalar() or 0

        scene_count = (
            await session.execute(
                select(func.count())
                .select_from(Scene)
                .where(Scene.creator_id == user_id)
            )
        ).scalar() or 0

        return UserDetailResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            email_verified=user.email_verified,
            credits=user.credits,
            is_admin=user.is_admin,
            can_create_character=user.can_create_character,
            can_create_scene=user.can_create_scene,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            character_count=char_count,
            scene_count=scene_count,
        )

    async def adjust_credits(
        self,
        session: AsyncSession,
        user_id: str,
        amount: int,
        reason: str,
        operator_id: str,
    ) -> None:
        """管理员积分调整（行级锁保护）。"""
        stmt = select(User.credits).where(User.id == user_id).with_for_update()
        result = await session.execute(stmt)
        current = result.scalar()
        if current is None:
            raise ResourceNotFoundError("User", user_id)

        if amount < 0 and current + amount < 0:
            raise CreditTransactionError(
                f"调整后余额为负: 当前 {current}, 调整 {amount}"
            )

        await session.execute(
            update(User).where(User.id == user_id)
            .values(credits=User.credits + amount)
        )
        session.add(
            Transaction(
                user_id=user_id,
                amount=amount,
                reason=f"Admin Adjust - {reason}",
                operator_id=operator_id,
            )
        )
        await session.flush()
        logger.info(
            "Admin adjust: user=%s amount=%d operator=%s reason=%s",
            user_id, amount, operator_id, reason,
        )

    async def update_user_permissions(
        self,
        session: AsyncSession,
        user_id: str,
        can_create_character: bool | None = None,
        can_create_scene: bool | None = None,
    ) -> dict:
        """更新用户创建权限。"""
        user = (
            await session.execute(select(User).where(User.id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise ResourceNotFoundError("User", user_id)

        if can_create_character is not None:
            user.can_create_character = can_create_character
        if can_create_scene is not None:
            user.can_create_scene = can_create_scene

        await session.flush()
        logger.info(
            "Permission update: user=%s char=%s scene=%s",
            user_id, can_create_character, can_create_scene,
        )
        return {
            "user_id": user_id,
            "can_create_character": user.can_create_character,
            "can_create_scene": user.can_create_scene,
            "message": "权限已更新",
        }

    async def get_user_recent_consumption(
        self,
        session: AsyncSession,
        user_id: str,
        days: int = 7,
    ) -> AdminUserConsumptionResponse:
        """查询用户近期积分消耗（总计 + 按天趋势 + 明细）。"""
        user = (
            await session.execute(select(User.id).where(User.id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise ResourceNotFoundError("User", user_id)

        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)

        # 获取时间范围内流水
        txn_stmt = (
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.created_at >= start,
            )
            .order_by(desc(Transaction.created_at))
        )
        transactions = list((await session.execute(txn_stmt)).scalars().all())

        # 聚合
        total_consumed = 0
        total_refunded = 0
        daily_map: dict[date, dict[str, int]] = defaultdict(
            lambda: {"consumed": 0, "refunded": 0, "net": 0}
        )

        for txn in transactions:
            d = txn.created_at.date()
            if txn.amount < 0:
                total_consumed += -txn.amount
                daily_map[d]["consumed"] += -txn.amount
            else:
                total_refunded += txn.amount
                daily_map[d]["refunded"] += txn.amount

        for d in daily_map:
            daily_map[d]["net"] = daily_map[d]["consumed"] - daily_map[d]["refunded"]

        daily = sorted(
            [
                AdminConsumptionDailyPoint(date=d, **vals)
                for d, vals in daily_map.items()
            ],
            key=lambda p: p.date,
        )

        recent_txns = [
            TransactionResponse(
                id=t.id,
                amount=t.amount,
                reason=t.reason,
                created_at=t.created_at,
            )
            for t in transactions[:50]
        ]

        return AdminUserConsumptionResponse(
            user_id=user_id,
            window_days=days,
            total_consumed=total_consumed,
            total_refunded=total_refunded,
            net_consumed=total_consumed - total_refunded,
            daily=daily,
            recent_transactions=recent_txns,
        )
