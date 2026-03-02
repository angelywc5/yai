"""验证令牌数据访问层。"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import VerificationToken

logger = logging.getLogger(__name__)


class VerificationTokenRepository:
    """验证令牌数据访问。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, email: str, expires_hours: int = 24) -> VerificationToken:
        """创建验证令牌（默认 24 小时过期）。"""
        token = VerificationToken(
            token=str(uuid.uuid4()),
            email=email,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_hours),
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(token)
        await self.session.flush()
        logger.info(f"验证令牌创建: {email} -> {token.token}")
        return token

    async def get_by_token(self, token: str) -> VerificationToken | None:
        """通过 token 查询。"""
        result = await self.session.execute(
            select(VerificationToken).where(VerificationToken.token == token)
        )
        return result.scalar_one_or_none()

    async def delete_by_token(self, token: str) -> None:
        """删除指定 token。"""
        stmt = delete(VerificationToken).where(VerificationToken.token == token)
        await self.session.execute(stmt)
        await self.session.flush()
        logger.info(f"验证令牌已删除: {token}")

    async def delete_expired(self) -> int:
        """清理过期令牌。"""
        stmt = delete(VerificationToken).where(
            VerificationToken.expires_at < datetime.now(timezone.utc)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        count = result.rowcount
        logger.info(f"清理过期令牌: {count} 条")
        return count
