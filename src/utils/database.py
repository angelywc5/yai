"""异步数据库引擎与会话管理。"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


class AsyncDatabaseEngine:
    """异步数据库引擎管理器。"""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def initialize(
        self,
        database_url: str,
        pool_min: int = 5,
        pool_max: int = 20,
        statement_timeout: int = 30000,
    ) -> None:
        """创建 AsyncEngine 和 session 工厂。"""
        connect_args = {
            "server_settings": {"statement_timeout": str(statement_timeout)}
        }
        self._engine = create_async_engine(
            database_url,
            pool_size=pool_max,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args=connect_args,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Database engine initialized (pool_max=%d)", pool_max)

    async def shutdown(self) -> None:
        """关闭连接池。"""
        if self._engine is not None:
            await self._engine.dispose()
            logger.info("Database engine disposed")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """生成异步数据库会话（用于 FastAPI Depends）。"""
        if self._session_factory is None:
            raise RuntimeError("Database engine not initialized")
        async with self._session_factory() as session:
            yield session

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("Database engine not initialized")
        return self._engine


db_engine = AsyncDatabaseEngine()
