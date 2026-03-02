"""YAI 平台 Pydantic Schema 定义 — 请求/响应 DTO。"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from typing import Generic, TypeVar

from pydantic import BaseModel, EmailStr, Field

# 泛型类型变量
T = TypeVar("T")

# ==================== 枚举类型 ====================


class ModelTier(str, Enum):
    """AI 模型档位。"""

    SPEED = "speed"
    PRO = "pro"
    ELITE = "elite"


# ==================== 用户相关 ====================


class UserRegisterRequest(BaseModel):
    """用户注册请求。"""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    username: str = Field(min_length=2, max_length=30, pattern=r"^[a-zA-Z0-9_-]+$")
    display_name: str = Field(min_length=1, max_length=50)


# 别名（向后兼容）
RegisterRequest = UserRegisterRequest


class UserLoginRequest(BaseModel):
    """用户登录请求。"""

    email: EmailStr
    password: str


# 别名（向后兼容）
LoginRequest = UserLoginRequest


class UserResponse(BaseModel):
    """用户响应。"""

    id: str
    email: str
    username: str
    display_name: str
    email_verified: bool
    credits: int
    is_admin: bool
    avatar_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== 角色定义子结构 ====================


class IdentitySchema(BaseModel):
    """角色身份定义。"""

    name: str
    background: str
    beliefs: str


class SpeechStyleSchema(BaseModel):
    """角色说话风格。"""

    tone: str
    catchphrases: list[str] = Field(default_factory=list)
    punctuation_habits: str = ""


class DialogueTurn(BaseModel):
    """示例对话轮次。"""

    user: str
    character: str


class CharacterDefinition(BaseModel):
    """角色完整定义。"""

    identity: IdentitySchema
    personality: list[str] = Field(min_length=3, max_length=5)
    speech_style: SpeechStyleSchema
    sample_dialogues: list[DialogueTurn] = Field(default_factory=list)


# ==================== 角色相关 ====================


class CharacterCreateRequest(BaseModel):
    """创建角色请求。"""

    name: str = Field(min_length=1, max_length=100)
    avatar_url: str | None = None
    avatar_source: str = Field(default="default", pattern=r"^(uploaded|default)$")
    tagline: str = Field(default="", max_length=200)
    definition: CharacterDefinition
    tags: list[str] = Field(default_factory=list, max_length=10)
    is_public: bool = False


class CharacterUpdateRequest(BaseModel):
    """更新角色请求。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_url: str | None = None
    avatar_source: str | None = Field(default=None, pattern=r"^(uploaded|default)$")
    tagline: str | None = Field(default=None, max_length=200)
    definition: CharacterDefinition | None = None
    tags: list[str] | None = Field(default=None, max_length=10)
    is_public: bool | None = None


class CharacterResponse(BaseModel):
    """角色响应（创建者可见完整 definition）。"""

    id: str
    name: str
    avatar_url: str | None
    avatar_source: str
    tagline: str
    definition: dict
    tags: list[str]
    is_public: bool
    chat_count: int
    like_count: int
    creator_id: str
    creator_username: str
    creator_display_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CharacterPublicResponse(BaseModel):
    """角色公开响应（非创建者仅可见精简信息）。"""

    id: str
    name: str
    avatar_url: str | None
    avatar_source: str
    tagline: str
    tags: list[str]
    personality_summary: list[str]
    is_public: bool
    chat_count: int
    like_count: int
    creator_id: str
    creator_username: str
    creator_display_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== 场景相关 ====================


class SceneCreateRequest(BaseModel):
    """创建场景请求。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=10, max_length=2000)
    cover_image_url: str | None = None
    cover_source: str = Field(default="default", pattern=r"^(uploaded|default)$")
    genre: str = Field(default="", max_length=100)
    time_period: str = Field(default="", max_length=100)
    setting_location: str = Field(default="", max_length=100)
    mood: str = Field(default="", max_length=100)
    scene_definition: str = Field(min_length=10, max_length=5000)
    player_objective: str = Field(default="", max_length=1000)
    greeting: str = Field(min_length=1, max_length=2000)
    allow_character_selection: bool = False
    character_ids: list[str] = Field(default_factory=list, max_length=10)
    tags: list[str] = Field(default_factory=list, max_length=10)
    is_public: bool = False


class SceneUpdateRequest(BaseModel):
    """更新场景请求。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    cover_image_url: str | None = None
    cover_source: str | None = Field(default=None, pattern=r"^(uploaded|default)$")
    genre: str | None = Field(default=None, max_length=100)
    time_period: str | None = Field(default=None, max_length=100)
    setting_location: str | None = Field(default=None, max_length=100)
    mood: str | None = Field(default=None, max_length=100)
    scene_definition: str | None = Field(default=None, min_length=10, max_length=5000)
    player_objective: str | None = Field(default=None, max_length=1000)
    greeting: str | None = Field(default=None, min_length=1, max_length=2000)
    allow_character_selection: bool | None = None
    tags: list[str] | None = Field(default=None, max_length=10)
    is_public: bool | None = None


class SceneCharacterRequest(BaseModel):
    """场景-角色关联请求。"""

    character_id: str
    role_in_scene: str = Field(default="", max_length=200)
    is_recommended: bool = False


class SceneResponse(BaseModel):
    """场景响应。"""

    id: str
    name: str
    description: str
    cover_image_url: str | None
    cover_source: str
    genre: str
    time_period: str
    setting_location: str
    mood: str
    player_objective: str
    greeting: str
    allow_character_selection: bool
    tags: list[str]
    is_public: bool
    play_count: int
    creator_id: str
    creator_username: str
    creator_display_name: str
    characters: list[CharacterPublicResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== 对话相关 ====================


class ChatDirective(BaseModel):
    """单轮输入修正指令。"""

    mode: str = Field(pattern=r"^(dialogue|aside|ooc|inner|camera|narration|continue)$")
    instruction: str = Field(default="", max_length=500)


class ChatRequest(BaseModel):
    """对话请求。"""

    character_id: str
    scene_id: str | None = None
    message: str = Field(min_length=1, max_length=4000)
    model_tier: ModelTier = ModelTier.SPEED
    session_id: str | None = None
    directives: list[ChatDirective] = Field(default_factory=list, max_length=5)


# ==================== 消息操作相关 ====================


class MessageEditRequest(BaseModel):
    """编辑消息请求。"""

    content: str = Field(min_length=1, max_length=4000)
    model_tier: ModelTier = ModelTier.SPEED


class MessageFeedbackRequest(BaseModel):
    """消息反馈请求。"""

    feedback: str = Field(pattern=r"^(like|dislike)$")


class MessageRegenerateRequest(BaseModel):
    """重新生成消息请求。"""

    model_tier: ModelTier = ModelTier.SPEED


class MessageForkRequest(BaseModel):
    """消息分叉请求。"""

    model_tier: ModelTier = ModelTier.SPEED


class MessageResponse(BaseModel):
    """消息响应。"""

    id: str
    role: str
    content: str
    token_count: int
    turn_number: int
    feedback: str | None
    is_pinned: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== 会话管理相关 ====================


class SessionResponse(BaseModel):
    """会话响应。"""

    session_id: str
    character_id: str
    character_name: str
    character_avatar_url: str | None
    last_message_preview: str
    last_message_at: datetime
    message_count: int
    created_at: datetime


class ChatHistoryPageResponse(BaseModel):
    """会话历史分页响应。"""

    session_id: str
    items: list[MessageResponse]
    has_more: bool
    next_before_message_id: str | None


# ==================== 用户自定义相关 ====================


class UserCustomizationRequest(BaseModel):
    """用户自定义请求。"""

    custom_prompt: str = Field(default="", max_length=2000)


class UserCustomizationResponse(BaseModel):
    """用户自定义响应。"""

    id: str
    user_id: str
    character_id: str
    custom_prompt: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== 最近对话角色 ====================


class RecentCharacterResponse(BaseModel):
    """最近对话角色响应。"""

    character_id: str
    character_name: str
    character_avatar_url: str | None
    character_tagline: str
    last_session_id: str
    last_message_preview: str
    last_message_at: datetime


# ==================== 积分相关 ====================


class CreditBalanceResponse(BaseModel):
    """积分余额响应。"""

    credits: int
    tier_pricing: dict[str, int]


class TransactionResponse(BaseModel):
    """积分流水响应。"""

    id: str
    amount: int
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== 搜索相关 ====================


class SearchRequest(BaseModel):
    """搜索请求。"""

    query: str = Field(min_length=1, max_length=100)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    category: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应封装。"""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int  # 总页数

    class Config:
        from_attributes = True


# ==================== 故事梗概相关 ====================


class StorySummaryResponse(BaseModel):
    """故事梗概响应。"""

    id: str
    from_turn: int
    to_turn: int
    summary: str
    key_dialogues: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== 管理相关 ====================


class AdminCreditAdjustRequest(BaseModel):
    """管理员积分调整请求。"""

    user_id: str = Field(description="目标用户 ID")
    amount: int
    reason: str = Field(min_length=1, max_length=500)


class AdminUserPermissionRequest(BaseModel):
    """管理员用户权限请求。"""

    can_create_character: bool | None = None
    can_create_scene: bool | None = None


class AdminConsumptionDailyPoint(BaseModel):
    """管理员用户消耗日报点。"""

    date: date
    consumed: int
    refunded: int
    net: int


class AdminUserConsumptionResponse(BaseModel):
    """管理员用户消耗响应。"""

    user_id: str
    window_days: int
    total_consumed: int
    total_refunded: int
    net_consumed: int
    daily: list[AdminConsumptionDailyPoint]
    recent_transactions: list[TransactionResponse]


class UserDetailResponse(BaseModel):
    """管理员查看的用户详情响应。"""

    id: str
    email: str
    username: str
    display_name: str
    email_verified: bool
    credits: int
    is_admin: bool
    can_create_character: bool
    can_create_scene: bool
    avatar_url: str | None = None
    created_at: datetime
    character_count: int = 0
    scene_count: int = 0

    model_config = {"from_attributes": True}


class ModelToggleRequest(BaseModel):
    """模型开关切换请求。"""

    enabled: bool


class ModelStatusResponse(BaseModel):
    """模型开关状态响应。"""

    speed: bool = True
    pro: bool = True
    elite: bool = True
