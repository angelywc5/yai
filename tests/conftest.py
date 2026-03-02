"""pytest 全局 fixtures 配置。"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import Settings, get_settings
from src.core.models import Base


# ============================================================================
# 测试配置
# ============================================================================

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SECRET_KEY = "test-secret-key-for-unit-tests"


@pytest.fixture
def anyio_backend() -> str:
    """指定 pytest-asyncio 使用的异步后端。"""
    return "asyncio"


# ============================================================================
# 数据库 Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def db_engine():
    """测试数据库引擎（SQLite 内存库，每次重建表）。"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """每个测试用例独立会话（自动回滚）。"""
    session_factory = async_sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


# ============================================================================
# Redis Mock Fixture
# ============================================================================


@pytest_asyncio.fixture
async def redis_client():
    """Mock Redis 客户端（单元测试无需真实 Redis）。"""
    mock = AsyncMock()
    mock.flushdb = AsyncMock()
    mock.aclose = AsyncMock()
    yield mock


# ============================================================================
# FastAPI TestClient Fixture
# ============================================================================


@pytest_asyncio.fixture
async def client(db_session, redis_client) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI 异步测试客户端。"""
    from main import app
    from src.api.deps import get_db_session

    async def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ============================================================================
# 工厂 Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def user_factory(db_session):
    """用户工厂：快速创建测试用户。"""
    from src.core.models import User
    from src.utils.security import PasswordHasher

    created_count = 0

    async def _create(
        email: str = "test@example.com",
        username: str = "testuser",
        display_name: str = "Test User",
        password: str = "testpassword123",
        credits: int = 500,
        email_verified: bool = True,
        is_admin: bool = False,
        can_create_character: bool = True,
        can_create_scene: bool = True,
    ) -> User:
        nonlocal created_count
        created_count += 1

        from cuid2 import cuid_wrapper
        generate_id = cuid_wrapper()

        user = User(
            id=generate_id(),
            email=email,
            username=username if created_count == 1 else f"{username}_{created_count}",
            display_name=display_name,
            password_hash=PasswordHasher.hash_password(password),
            credits=credits,
            email_verified=email_verified,
            is_admin=is_admin,
            can_create_character=can_create_character,
            can_create_scene=can_create_scene,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create


@pytest_asyncio.fixture
async def character_factory(db_session):
    """角色工厂：快速创建测试角色。"""
    from src.core.models import Character

    async def _create(
        creator_id: str,
        name: str = "测试角色",
        is_public: bool = True,
    ) -> Character:
        from cuid2 import cuid_wrapper
        generate_id = cuid_wrapper()

        character = Character(
            id=generate_id(),
            name=name,
            avatar_url=None,
            avatar_source="default",
            tagline="测试角色简介",
            definition={
                "identity": {
                    "name": name,
                    "background": "测试背景",
                    "beliefs": "测试信念",
                },
                "personality": ["温柔", "善良", "聪明"],
                "speech_style": {
                    "tone": "温和",
                    "catchphrases": ["嗯嗯"],
                    "punctuation_habits": "...",
                },
                "sample_dialogues": [],
            },
            tags=["测试"],
            is_public=is_public,
            creator_id=creator_id,
        )
        db_session.add(character)
        await db_session.commit()
        await db_session.refresh(character)
        return character

    return _create


# ============================================================================
# Settings Fixture
# ============================================================================


@pytest.fixture
def test_settings() -> Settings:
    """测试用 Settings 配置。"""
    return Settings(
        database_url=TEST_DATABASE_URL,
        redis_url="redis://localhost:6379/1",
        jwt_secret_key=TEST_SECRET_KEY,
        debug=True,
        environment="test",
    )
