"""用户数据访问层。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import User
from src.utils.id_generator import new_id

logger = logging.getLogger(__name__)


class UserRepository:
    """用户数据访问。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, email: str, password_hash: str, username: str, display_name: str
    ) -> User:
        """创建新用户（初始状态：未验证、0 积分、非管理员）。"""
        user = User(
            id=new_id(),
            email=email,
            password_hash=password_hash,
            username=username,
            display_name=display_name,
            email_verified=False,
            credits=0,
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(user)
        await self.session.flush()
        logger.info(f"用户创建成功: {user.id} ({email})")
        return user

    async def get_by_id(self, session: AsyncSession, user_id: str) -> User | None:
        """通过 ID 查询用户。"""
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """通过邮箱查询用户。"""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """通过用户名查询用户。"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def activate_user(self, email: str, default_credits: int) -> User:
        """激活用户并发放默认积分。"""
        stmt = (
            update(User)
            .where(User.email == email)
            .values(email_verified=True, credits=default_credits)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one()
        await self.session.flush()
        logger.info(f"用户激活成功: {user.id} ({email}), 积分: {default_credits}")
        return user

    async def set_admin_by_email(self, email: str, is_admin: bool) -> User:
        """设置用户管理员权限。"""
        stmt = (
            update(User)
            .where(User.email == email)
            .values(is_admin=is_admin)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one()
        await self.session.flush()
        logger.info(f"用户权限更新: {user.id} ({email}), is_admin={is_admin}")
        return user

    async def update_credits(self, user_id: str, delta: int) -> None:
        """
        更新用户积分（增量更新）。

        Args:
            user_id: 用户 ID
            delta: 积分变动量（正数为增加，负数为扣减）
        """
        stmt = (
            update(User).where(User.id == user_id).values(credits=User.credits + delta)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_credits_for_update(self, user_id: str) -> int:
        """查询积分（行级锁）。"""
        stmt = select(User.credits).where(User.id == user_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one()
