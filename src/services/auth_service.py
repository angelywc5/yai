"""认证业务流程编排。"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from src.config.settings import Settings
from src.core.exceptions import (
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    UnauthorizedError,
    UsernameAlreadyExistsError,
)
from src.core.models import User
from src.repositories.token_repo import VerificationTokenRepository
from src.repositories.user_repo import UserRepository
from src.services.email_service import EmailService
from src.utils.security import JwtTokenManager, PasswordHasher

logger = logging.getLogger(__name__)


class AuthService:
    """认证业务编排。"""

    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: VerificationTokenRepository,
        email_service: EmailService,
        password_hasher: PasswordHasher,
        jwt_manager: JwtTokenManager,
        settings: Settings,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.email_service = email_service
        self.password_hasher = password_hasher
        self.jwt_manager = jwt_manager
        self.settings = settings

    async def register(
        self, email: str, password: str, username: str, display_name: str
    ) -> User:
        """
        用户注册流程。

        1. 校验邮箱唯一性
        2. 校验用户名唯一性
        3. 哈希密码
        4. 创建用户（未验证状态）
        5. 生成验证令牌
        6. 异步发送验证邮件

        Raises:
            EmailAlreadyExistsError: 邮箱已被注册
            UsernameAlreadyExistsError: 用户名已被注册
        """
        # 校验邮箱唯一性
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise EmailAlreadyExistsError()

        # 校验用户名唯一性
        existing_username = await self.user_repo.get_by_username(username)
        if existing_username:
            raise UsernameAlreadyExistsError()

        # 哈希密码
        password_hash = self.password_hasher.hash_password(password)

        # 创建用户
        user = await self.user_repo.create(email, password_hash, username, display_name)

        # 生成验证令牌
        token = await self.token_repo.create(
            email, self.settings.verification_token_expire_hours
        )

        # 异步发送验证邮件（不阻塞）
        asyncio.create_task(
            self.email_service.send_verification_email(email, token.token)
        )

        logger.info(f"用户注册成功: {user.id} ({email})")
        return user

    async def verify_email(self, token: str) -> User:
        """
        邮箱验证流程。

        1. 校验 token
        2. 激活用户并发放默认积分
        3. 若符合自动提权条件，设置管理员权限
        4. 删除一次性验证 token

        Raises:
            TokenInvalidError: Token 不存在
            TokenExpiredError: Token 已过期
        """
        # 查询 token
        verification_token = await self.token_repo.get_by_token(token)
        if not verification_token:
            raise TokenInvalidError()

        # 校验过期时间
        if verification_token.expires_at < datetime.now(timezone.utc):
            raise TokenExpiredError()

        # 激活用户
        user = await self.user_repo.activate_user(
            verification_token.email, self.settings.default_credits
        )

        # 自动提权（管理员白名单）
        if (
            self.settings.admin_auto_promote_on_verify
            and user.email in self.settings.admin_email_allowlist
        ):
            user = await self.user_repo.set_admin_by_email(user.email, True)
            logger.info(f"管理员自动提权: {user.id} ({user.email})")

        # 删除 token（一次性使用）
        await self.token_repo.delete_by_token(token)

        logger.info(f"邮箱验证成功: {user.id} ({user.email})")
        return user

    async def login(self, email: str, password: str) -> tuple[str, str]:
        """
        登录流程。

        返回: (access_token, refresh_token)

        Raises:
            InvalidCredentialsError: 邮箱或密码错误
            EmailNotVerifiedError: 邮箱未验证
        """
        # 查询用户
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError()

        # 验证密码
        if not self.password_hasher.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        # 校验邮箱已验证
        if not user.email_verified:
            raise EmailNotVerifiedError()

        # 生成 Token
        access_token = self.jwt_manager.create_access_token(
            user.id, self.settings.access_token_expire_minutes
        )
        refresh_token = self.jwt_manager.create_refresh_token(
            user.id, self.settings.refresh_token_expire_minutes
        )

        logger.info(f"用户登录成功: {user.id} ({email})")
        return access_token, refresh_token

    async def refresh_token(self, refresh_token: str) -> str:
        """
        刷新 Access Token。

        Raises:
            TokenInvalidError: Token 无效或类型不匹配
            TokenExpiredError: Token 已过期
        """
        # 解析 refresh_token
        payload = self.jwt_manager.decode_token(refresh_token, token_type="refresh")

        # 生成新的 access_token
        new_access_token = self.jwt_manager.create_access_token(
            payload["sub"], self.settings.access_token_expire_minutes
        )

        logger.info(f"Token 刷新成功: user_id={payload['sub']}")
        return new_access_token

    async def get_current_user(self, access_token: str) -> User:
        """
        从 Access Token 获取当前用户。

        Raises:
            UnauthorizedError: Token 无效或用户不存在
        """
        # 解析 token
        try:
            payload = self.jwt_manager.decode_token(access_token, token_type="access")
        except (TokenExpiredError, TokenInvalidError) as e:
            raise UnauthorizedError(str(e)) from e

        # 查询用户
        user = await self.user_repo.get_by_id(payload["sub"])
        if not user or not user.email_verified:
            raise UnauthorizedError("账号不存在或未验证")

        return user
