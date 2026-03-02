"""YAI 平台配置管理 — 使用 pydantic-settings 从 .env 文件加载配置。"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """应用基础配置"""

    app_name: str = "YAI"
    debug: bool = False
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]


class DatabaseSettings(BaseSettings):
    """数据库连接配置"""

    database_url: str = "postgresql+asyncpg://yai:yai@localhost:5432/yai"
    db_pool_min_size: int = 5
    db_pool_max_size: int = 20
    db_statement_timeout: int = 30000


class RedisSettings(BaseSettings):
    """Redis 连接配置"""

    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 20


class JwtSettings(BaseSettings):
    """JWT 认证配置"""

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 10080
    jwt_refresh_token_expire_minutes: int = 20160


class GeminiSettings(BaseSettings):
    """Gemini AI 模型配置"""

    gemini_api_key: str = ""
    gemini_speed_model: str = "gemini-3-flash"
    gemini_pro_model: str = "gemini-2.5-pro"
    gemini_elite_model: str = "gemini-3.1-pro"
    gemini_request_timeout: int = 30
    gemini_embedding_model: str = "text-embedding-004"


class SmtpSettings(BaseSettings):
    """邮件服务配置"""

    smtp_provider: str = "resend"
    smtp_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_from_email: str = "noreply@yai.app"
    verification_url_base: str = "https://yai.app/verify"
    verification_token_expire_hours: int = 24


class AdminSettings(BaseSettings):
    """管理员配置"""

    admin_email_allowlist: list[str] = []
    admin_auto_promote_on_verify: bool = True
    admin_bootstrap_enabled: bool = False
    admin_bootstrap_token: str = ""


class CreditSettings(BaseSettings):
    """积分定价配置"""

    default_credits: int = 500
    speed_credits_per_1k_tokens: int = 10
    pro_credits_per_1k_tokens: int = 50
    elite_credits_per_1k_tokens: int = 150
    credit_hold_multiplier: float = 1.5
    credit_hold_default_tokens: int = 1000


class MemorySettings(BaseSettings):
    """记忆系统配置"""

    max_short_term_messages: int = 20
    max_long_term_fragments: int = 5
    max_story_summaries: int = 3
    chat_history_initial_rounds: int = 20
    chat_history_page_rounds: int = 20
    embedding_dimension: int = 768
    embedding_provider: str = "gemini"
    sentence_transformer_model: str = "all-MiniLM-L6-v2"


class StorySummarySettings(BaseSettings):
    """故事梗概配置"""

    summary_trigger_interval: int = 10
    summary_max_key_dialogues: int = 5
    summary_model_tier: str = "speed"
    summary_max_length: int = 200
    chat_response_target_tokens: int = 800
    chat_response_hard_cap_tokens: int = 1200


class RateLimitSettings(BaseSettings):
    """限流配置"""

    rate_limit_chat_max: int = 10
    rate_limit_chat_window: int = 60
    rate_limit_auth_max: int = 5
    rate_limit_auth_window: int = 60
    rate_limit_upload_max: int = 20
    rate_limit_upload_window: int = 3600
    rate_limit_default_max: int = 60
    rate_limit_default_window: int = 60


class SceneSettings(BaseSettings):
    """场景配置"""

    max_scene_characters: int = 10
    max_scene_definition_length: int = 5000
    max_scene_greeting_length: int = 2000
    max_scene_metadata_length: int = 100
    max_scene_tags: int = 10
    max_scene_player_objective_length: int = 1000


class UploadSettings(BaseSettings):
    """图片上传配置"""

    upload_dir: str = "static/uploads"
    max_upload_size_mb: int = 5
    allowed_image_types: list[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
    ]
    avatar_resize_px: int = 256
    cover_resize_width: int = 800
    cover_resize_height: int = 450
    default_avatars_dir: str = "static/defaults/avatars"
    default_covers_dir: str = "static/defaults/covers"


class MessageSettings(BaseSettings):
    """消息操作配置"""

    max_pinned_messages_per_character: int = 20
    max_custom_prompt_length: int = 2000
    max_tags_per_character: int = 10
    max_tag_length: int = 20
    recent_characters_limit: int = 20
    session_preview_length: int = 100
    username_min_length: int = 2
    username_max_length: int = 30


class Settings(
    AppSettings,
    DatabaseSettings,
    RedisSettings,
    JwtSettings,
    GeminiSettings,
    SmtpSettings,
    AdminSettings,
    CreditSettings,
    MemorySettings,
    StorySummarySettings,
    RateLimitSettings,
    SceneSettings,
    UploadSettings,
    MessageSettings,
):
    """聚合所有配置域的最终 Settings 类。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """全局单例获取 Settings，避免重复读取 .env 文件。"""
    return Settings()
