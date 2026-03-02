"""YAI 业务异常定义。"""

from __future__ import annotations


class YaiBaseError(Exception):
    """YAI 业务异常基类。"""

    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)


# ============================================================================
# 认证相关异常
# ============================================================================


class EmailAlreadyExistsError(YaiBaseError):
    """邮箱已被注册。"""

    def __init__(self):
        super().__init__("该邮箱已被注册", "AUTH_EMAIL_EXISTS")


class UsernameAlreadyExistsError(YaiBaseError):
    """用户名已被注册。"""

    def __init__(self):
        super().__init__("该用户名已被注册", "AUTH_USERNAME_EXISTS")


class InvalidCredentialsError(YaiBaseError):
    """邮箱或密码错误。"""

    def __init__(self):
        super().__init__("邮箱或密码错误", "AUTH_INVALID_CREDENTIALS")


class EmailNotVerifiedError(YaiBaseError):
    """邮箱未验证。"""

    def __init__(self):
        super().__init__("请先验证邮箱", "AUTH_EMAIL_NOT_VERIFIED")


class TokenExpiredError(YaiBaseError):
    """验证令牌已过期。"""

    def __init__(self):
        super().__init__("验证令牌已过期，请重新注册", "AUTH_TOKEN_EXPIRED")


class TokenInvalidError(YaiBaseError):
    """无效的令牌。"""

    def __init__(self):
        super().__init__("无效的令牌", "AUTH_TOKEN_INVALID")


class UnauthorizedError(YaiBaseError):
    """未登录或 Token 无效。"""

    def __init__(self, message: str = "未登录"):
        super().__init__(message, "AUTH_UNAUTHORIZED")


class ForbiddenError(YaiBaseError):
    """权限不足。"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message, "AUTH_FORBIDDEN")


# ============================================================================
# 积分相关异常
# ============================================================================


class InsufficientCreditsError(YaiBaseError):
    """积分不足。"""

    def __init__(self, required: int, available: int):
        super().__init__(
            f"积分不足，需要 {required} 积分，当前余额 {available}",
            "CREDIT_INSUFFICIENT",
        )
        self.required = required
        self.available = available


class CreditHoldNotFoundError(YaiBaseError):
    """预扣记录不存在。"""

    def __init__(self, hold_id: str):
        super().__init__(f"预扣记录不存在: {hold_id}", "CREDIT_HOLD_NOT_FOUND")


class CreditTransactionError(YaiBaseError):
    """积分事务异常。"""

    def __init__(self, detail: str):
        super().__init__(f"积分事务异常: {detail}", "CREDIT_TRANSACTION_ERROR")


# ============================================================================
# 资源相关异常
# ============================================================================


class ResourceNotFoundError(YaiBaseError):
    """资源不存在。"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            f"{resource_type} (ID: {resource_id}) 不存在",
            "RESOURCE_NOT_FOUND",
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceDeletedError(YaiBaseError):
    """资源已被删除。"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            f"{resource_type} (ID: {resource_id}) 已被删除",
            "RESOURCE_DELETED",
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


# ============================================================================
# 角色相关异常
# ============================================================================


class CharacterNotFoundError(YaiBaseError):
    """角色不存在。"""

    def __init__(self, character_id: str):
        super().__init__(f"角色不存在: {character_id}", "CHAR_NOT_FOUND")


class CharacterPermissionError(YaiBaseError):
    """无权操作此角色。"""

    def __init__(self):
        super().__init__("无权操作此角色", "CHAR_PERMISSION_DENIED")


class CharacterDefinitionError(YaiBaseError):
    """角色定义校验失败。"""

    def __init__(self, detail: str):
        super().__init__(f"角色定义校验失败: {detail}", "CHAR_DEFINITION_INVALID")


class CharacterCreationForbiddenError(YaiBaseError):
    """角色创建权限被禁用。"""

    def __init__(self):
        super().__init__("您的角色创建权限已被管理员禁用", "CHAR_CREATION_FORBIDDEN")


# ============================================================================
# 场景相关异常
# ============================================================================


class SceneNotFoundError(YaiBaseError):
    """场景不存在。"""

    def __init__(self, scene_id: str):
        super().__init__(f"场景不存在: {scene_id}", "SCENE_NOT_FOUND")


class ScenePermissionError(YaiBaseError):
    """无权操作此场景。"""

    def __init__(self):
        super().__init__("无权操作此场景", "SCENE_PERMISSION_DENIED")


class SceneCreationForbiddenError(YaiBaseError):
    """场景创建权限被禁用。"""

    def __init__(self):
        super().__init__("您的场景创建权限已被管理员禁用", "SCENE_CREATION_FORBIDDEN")


class SceneCharacterLimitError(YaiBaseError):
    """场景角色数量已达上限。"""

    def __init__(self, limit: int):
        super().__init__(f"场景角色数量已达上限({limit})", "SCENE_CHARACTER_LIMIT")


class SceneCharacterNotAccessibleError(YaiBaseError):
    """角色不可用(非公开或非自己创建)。"""

    def __init__(self, character_id: str):
        super().__init__(
            f"角色不可用(非公开或非自己创建): {character_id}",
            "SCENE_CHARACTER_NOT_ACCESSIBLE",
        )


# ============================================================================
# 对话相关异常
# ============================================================================


class ModelProviderError(YaiBaseError):
    """模型调用异常。"""

    def __init__(self, detail: str):
        super().__init__(f"模型调用异常: {detail}", "MODEL_PROVIDER_ERROR")


class ModelTimeoutError(YaiBaseError):
    """模型响应超时。"""

    def __init__(self):
        super().__init__("模型响应超时", "MODEL_TIMEOUT")


class SessionNotFoundError(YaiBaseError):
    """会话不存在。"""

    def __init__(self, session_id: str):
        super().__init__(f"会话不存在: {session_id}", "CHAT_SESSION_NOT_FOUND")


class YamlParseError(YaiBaseError):
    """YAML 响应解析失败。"""

    def __init__(self, detail: str):
        super().__init__(f"YAML 响应解析失败: {detail}", "YAML_PARSE_ERROR")


class MessageNotFoundError(YaiBaseError):
    """消息不存在。"""

    def __init__(self, message_id: str):
        super().__init__(f"消息不存在: {message_id}", "MESSAGE_NOT_FOUND")


class MessagePermissionError(YaiBaseError):
    """无权操作此消息。"""

    def __init__(self):
        super().__init__("无权操作此消息", "MESSAGE_PERMISSION_DENIED")


class MessageEditNotAllowedError(YaiBaseError):
    """只能编辑自己的 user 角色消息。"""

    def __init__(self):
        super().__init__("只能编辑自己的 user 角色消息", "MESSAGE_EDIT_NOT_ALLOWED")


class MessageFeedbackNotAllowedError(YaiBaseError):
    """只能对 AI 回复进行评价。"""

    def __init__(self):
        super().__init__("只能对 AI 回复进行评价", "MESSAGE_FEEDBACK_NOT_ALLOWED")


# ============================================================================
# 限流相关异常
# ============================================================================


class RateLimitExceededError(YaiBaseError):
    """请求过于频繁。"""

    def __init__(self, retry_after: int):
        super().__init__(
            f"请求过于频繁，请 {retry_after} 秒后重试",
            "RATE_LIMIT_EXCEEDED",
        )
        self.retry_after = retry_after


class ModelDisabledError(YaiBaseError):
    """模型档位已被禁用。"""

    def __init__(self, tier: str):
        super().__init__(f"模型 {tier} 当前已禁用", "MODEL_DISABLED")
