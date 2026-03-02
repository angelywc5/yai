"""积分计算引擎 — 纯计算逻辑，无 I/O 操作。"""

import math
from dataclasses import dataclass

from src.core.schemas import ModelTier


@dataclass(frozen=True)
class TierPricing:
    """档位定价配置。"""

    tier: ModelTier
    credits_per_1k_tokens: int


@dataclass
class CreditHold:
    """预扣凭证。"""

    hold_id: str
    user_id: str
    tier: ModelTier
    estimated_amount: int


@dataclass
class CreditSettlement:
    """结算结果。"""

    hold: CreditHold
    actual_tokens_used: int
    actual_amount: int
    refund: int


class CreditEngine:
    """
    积分计算引擎 — 纯函数，无 I/O，定价从配置注入。

    职责：
    - 梯度定价计算
    - Token 费用估算
    - 预扣金额计算
    - 余额校验
    """

    def __init__(
        self,
        speed_price: int,
        pro_price: int,
        elite_price: int,
        hold_multiplier: float,
        hold_default_tokens: int,
    ):
        """
        初始化积分引擎。

        Args:
            speed_price: Speed 档位每 1k tokens 积分消耗
            pro_price: Pro 档位每 1k tokens 积分消耗
            elite_price: Elite 档位每 1k tokens 积分消耗
            hold_multiplier: 预扣倍率（例如 1.5 表示预扣 1.5 倍估算值）
            hold_default_tokens: 默认预估 token 数（无明确估算时使用）
        """
        self.tier_pricing: dict[ModelTier, TierPricing] = {
            ModelTier.SPEED: TierPricing(ModelTier.SPEED, speed_price),
            ModelTier.PRO: TierPricing(ModelTier.PRO, pro_price),
            ModelTier.ELITE: TierPricing(ModelTier.ELITE, elite_price),
        }
        self._hold_multiplier = hold_multiplier
        self._hold_default_tokens = hold_default_tokens

    def estimate_hold_amount(
        self, tier: ModelTier, estimated_tokens: int | None = None
    ) -> int:
        """
        计算预扣金额。

        预扣金额 = ceil(预估tokens / 1000) * 单价 * 预扣倍率

        Args:
            tier: 模型档位
            estimated_tokens: 预估 token 数（None 时使用 hold_default_tokens）

        Returns:
            预扣积分数量
        """
        tokens = estimated_tokens or self._hold_default_tokens
        pricing = self.tier_pricing[tier]
        base_cost = math.ceil(tokens / 1000) * pricing.credits_per_1k_tokens
        return math.ceil(base_cost * self._hold_multiplier)

    def calculate_actual_cost(self, tier: ModelTier, actual_tokens: int) -> int:
        """
        计算实际消耗。

        实际消耗 = ceil(实际tokens / 1000) * 单价

        Args:
            tier: 模型档位
            actual_tokens: 实际 token 数

        Returns:
            实际积分消耗
        """
        pricing = self.tier_pricing[tier]
        return math.ceil(actual_tokens / 1000) * pricing.credits_per_1k_tokens

    def calculate_refund(self, estimated: int, actual: int) -> int:
        """
        计算退还差额。

        退还 = max(0, 预扣金额 - 实际消耗)

        Args:
            estimated: 预扣金额
            actual: 实际消耗

        Returns:
            应退还积分数量
        """
        return max(0, estimated - actual)

    def validate_balance(self, balance: int, required: int) -> bool:
        """
        校验余额是否充足。

        Args:
            balance: 当前余额
            required: 所需积分

        Returns:
            True 表示余额充足
        """
        return balance >= required

    def get_tier_pricing(self, tier: ModelTier) -> TierPricing:
        """
        获取档位定价。

        Args:
            tier: 模型档位

        Returns:
            档位定价配置

        Raises:
            KeyError: 档位不存在
        """
        return self.tier_pricing[tier]

    def get_all_pricing(self) -> dict[str, int]:
        """
        获取所有档位定价。

        Returns:
            档位名称到积分消耗的映射
        """
        return {
            tier.value: pricing.credits_per_1k_tokens
            for tier, pricing in self.tier_pricing.items()
        }
