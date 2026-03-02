"""YAI 平台 SQLAlchemy ORM 模型定义。"""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.utils.id_generator import generate_cuid


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。"""


class TimestampMixin:
    """时间戳混入：created_at / updated_at。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(TimestampMixin, Base):
    """用户模型。"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(25), primary_key=True, default=generate_cuid)
    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    credits: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    can_create_character: Mapped[bool] = mapped_column(Boolean, default=True)
    can_create_scene: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    characters: Mapped[list[Character]] = relationship(
        back_populates="creator", cascade="all, delete-orphan"
    )
    scenes: Mapped[list[Scene]] = relationship(
        back_populates="creator", cascade="all, delete-orphan"
    )
    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    customizations: Mapped[list[UserCharacterCustomization]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Character(TimestampMixin, Base):
    """角色模型。"""

    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(25), primary_key=True, default=generate_cuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    avatar_source: Mapped[str] = mapped_column(String(20), default="default")
    tagline: Mapped[str] = mapped_column(String(200), default="")
    definition: Mapped[dict] = mapped_column(JSON, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    chat_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    like_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    creator_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    # 关系
    creator: Mapped[User] = relationship(back_populates="characters")
    messages: Mapped[list[Message]] = relationship(back_populates="character")
    scene_characters: Mapped[list[SceneCharacter]] = relationship(
        back_populates="character"
    )
    customizations: Mapped[list[UserCharacterCustomization]] = relationship(
        back_populates="character"
    )


class Scene(TimestampMixin, Base):
    """场景模型。"""

    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(25), primary_key=True, default=generate_cuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    cover_source: Mapped[str] = mapped_column(String(20), default="default")
    genre: Mapped[str] = mapped_column(String(100), default="")
    time_period: Mapped[str] = mapped_column(String(100), default="")
    setting_location: Mapped[str] = mapped_column(String(100), default="")
    mood: Mapped[str] = mapped_column(String(100), default="")
    scene_definition: Mapped[str] = mapped_column(Text, nullable=False)
    player_objective: Mapped[str] = mapped_column(String(1000), default="")
    greeting: Mapped[str] = mapped_column(Text, nullable=False)
    allow_character_selection: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    play_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    creator_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    # 关系
    creator: Mapped[User] = relationship(back_populates="scenes")
    scene_characters: Mapped[list[SceneCharacter]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )


class SceneCharacter(Base):
    """场景-角色关联模型。"""

    __tablename__ = "scene_characters"

    id: Mapped[str] = mapped_column(String(25), primary_key=True, default=generate_cuid)
    scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_in_scene: Mapped[str] = mapped_column(String(200), default="")
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 关系
    scene: Mapped[Scene] = relationship(back_populates="scene_characters")
    character: Mapped[Character] = relationship(back_populates="scene_characters")

    __table_args__ = (
        UniqueConstraint("scene_id", "character_id", name="uq_scene_character"),
    )


class Transaction(Base):
    """积分流水模型。"""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(25), primary_key=True, default=generate_cuid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    operator_id: Mapped[str | None] = mapped_column(String(25))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # 关系
    user: Mapped[User] = relationship(back_populates="transactions")


class VerificationToken(Base):
    """邮箱验证令牌模型。"""

    __tablename__ = "verification_tokens"

    id: Mapped[str] = mapped_column(String(25), primary_key=True, default=generate_cuid)
    token: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Message(Base):
    """对话消息模型。"""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(25), primary_key=True, default=generate_cuid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.id"), nullable=False, index=True
    )
    scene_id: Mapped[str | None] = mapped_column(
        ForeignKey("scenes.id"), nullable=True, index=True
    )
    session_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(768), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    turn_number: Mapped[int] = mapped_column(Integer, default=0)
    feedback: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 关系
    character: Mapped[Character] = relationship(back_populates="messages")


class StorySummary(Base):
    """故事梗概模型。"""

    __tablename__ = "story_summaries"

    id: Mapped[str] = mapped_column(String(25), primary_key=True, default=generate_cuid)
    session_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.id"), nullable=False
    )
    scene_id: Mapped[str | None] = mapped_column(ForeignKey("scenes.id"), nullable=True)
    from_turn: Mapped[int] = mapped_column(Integer, nullable=False)
    to_turn: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_dialogues: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(768), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UserCharacterCustomization(TimestampMixin, Base):
    """用户-角色自定义配置模型。"""

    __tablename__ = "user_character_customizations"

    id: Mapped[str] = mapped_column(String(25), primary_key=True, default=generate_cuid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.id"), nullable=False, index=True
    )
    custom_prompt: Mapped[str] = mapped_column(Text, default="")

    # 关系
    user: Mapped[User] = relationship(back_populates="customizations")
    character: Mapped[Character] = relationship(back_populates="customizations")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "character_id", name="uq_user_character_customization"
        ),
    )
