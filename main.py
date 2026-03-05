"""YAI 拟人化 AI 对话平台 — FastAPI 应用入口。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings
from src.utils.database import db_engine
from src.utils.logger import setup_logging
from src.utils.redis_client import redis_manager


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期管理：启动时初始化资源，关闭时释放资源。"""
    settings = get_settings()

    # 启动时初始化
    setup_logging(settings.environment, log_level="DEBUG" if settings.debug else "INFO")

    await db_engine.initialize(
        database_url=settings.database_url,
        pool_min=settings.db_pool_min_size,
        pool_max=settings.db_pool_max_size,
        statement_timeout=settings.db_statement_timeout,
    )

    await redis_manager.initialize(
        redis_url=settings.redis_url,
        max_connections=settings.redis_max_connections,
    )

    yield

    # 关闭时清理
    await redis_manager.shutdown()
    await db_engine.shutdown()


# 创建 FastAPI 应用实例
app = FastAPI(
    title="YAI API",
    description="拟人化 AI 对话平台后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

# 注册中间件（模块级别，应用启动前完成）
from src.api.middleware import RateLimitMiddleware, RequestLogMiddleware

settings = get_settings()

app.add_middleware(RequestLogMiddleware)
app.add_middleware(RateLimitMiddleware, redis_manager=redis_manager)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查端点
@app.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查端点。"""
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    """根路径欢迎消息。"""
    return {"message": "Welcome to YAI API", "version": "1.0.0"}


# 挂载路由
from src.api.admin_routes import router as admin_router
from src.api.auth_routes import router as auth_router
from src.api.character_routes import router as character_router
from src.api.chat_routes import router as chat_router
from src.api.credit_routes import router as credit_router
from src.api.scene_routes import router as scene_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(character_router, prefix="/api/v1/characters", tags=["Characters"])
app.include_router(scene_router, prefix="/api/v1/scenes", tags=["Scenes"])
app.include_router(credit_router, prefix="/api/v1/credits", tags=["Credits"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
