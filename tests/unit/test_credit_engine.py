"""积分引擎单元测试。"""

import pytest

from src.core.credit_engine import CreditEngine, CreditHold, CreditSettlement
from src.core.schemas import ModelTier


@pytest.fixture
def engine() -> CreditEngine:
    """创建默认配置的积分引擎。"""
    return CreditEngine(
        speed_price=10,
        pro_price=50,
        elite_price=150,
        hold_multiplier=1.5,
        hold_default_tokens=1000,
    )


class TestCalculateActualCost:
    """测试实际消耗计算。"""

    def test_speed_tier_1000_tokens(self, engine: CreditEngine) -> None:
        """Speed 档 1000 tokens → 10 积分。"""
        cost = engine.calculate_actual_cost(ModelTier.SPEED, 1000)
        assert cost == 10

    def test_pro_tier_1000_tokens(self, engine: CreditEngine) -> None:
        """Pro 档 1000 tokens → 50 积分。"""
        cost = engine.calculate_actual_cost(ModelTier.PRO, 1000)
        assert cost == 50

    def test_elite_tier_1000_tokens(self, engine: CreditEngine) -> None:
        """Elite 档 1000 tokens → 150 积分。"""
        cost = engine.calculate_actual_cost(ModelTier.ELITE, 1000)
        assert cost == 150

    def test_partial_tokens_rounds_up(self, engine: CreditEngine) -> None:
        """800 tokens 向上取整按 1k 计费 → ceil(800/1000) = 1 → 10 积分。"""
        cost = engine.calculate_actual_cost(ModelTier.SPEED, 800)
        assert cost == 10

    def test_1001_tokens_rounds_up(self, engine: CreditEngine) -> None:
        """1001 tokens → ceil(1001/1000) = 2 → 20 积分 (Speed)。"""
        cost = engine.calculate_actual_cost(ModelTier.SPEED, 1001)
        assert cost == 20

    def test_zero_tokens(self, engine: CreditEngine) -> None:
        """0 tokens → 0 积分。"""
        cost = engine.calculate_actual_cost(ModelTier.SPEED, 0)
        assert cost == 0

    def test_large_token_count(self, engine: CreditEngine) -> None:
        """5000 tokens Pro 档 → 5 * 50 = 250 积分。"""
        cost = engine.calculate_actual_cost(ModelTier.PRO, 5000)
        assert cost == 250


class TestEstimateHoldAmount:
    """测试预扣金额计算。"""

    def test_with_default_tokens(self, engine: CreditEngine) -> None:
        """未指定 estimated_tokens 时使用 hold_default_tokens=1000。
        Speed: ceil(1000/1000) * 10 * 1.5 = 15
        """
        hold = engine.estimate_hold_amount(ModelTier.SPEED)
        assert hold == 15

    def test_with_explicit_tokens(self, engine: CreditEngine) -> None:
        """显式指定 2000 tokens, Pro 档: ceil(2000/1000) * 50 * 1.5 = 150。"""
        hold = engine.estimate_hold_amount(ModelTier.PRO, estimated_tokens=2000)
        assert hold == 150

    def test_hold_multiplier_applied(self, engine: CreditEngine) -> None:
        """Elite 1000 tokens: ceil(1000/1000) * 150 * 1.5 = 225。"""
        hold = engine.estimate_hold_amount(ModelTier.ELITE, estimated_tokens=1000)
        assert hold == 225

    def test_partial_tokens_hold(self, engine: CreditEngine) -> None:
        """800 tokens Speed: ceil(800/1000) * 10 * 1.5 = ceil(15) = 15。"""
        hold = engine.estimate_hold_amount(ModelTier.SPEED, estimated_tokens=800)
        assert hold == 15

    def test_hold_rounds_up(self, engine: CreditEngine) -> None:
        """1500 tokens Speed: ceil(1500/1000) * 10 * 1.5 = 2 * 10 * 1.5 = 30。"""
        hold = engine.estimate_hold_amount(ModelTier.SPEED, estimated_tokens=1500)
        assert hold == 30


class TestCalculateRefund:
    """测试退还差额计算。"""

    def test_normal_refund(self, engine: CreditEngine) -> None:
        """预扣 150 实际 80 → 退还 70。"""
        refund = engine.calculate_refund(estimated=150, actual=80)
        assert refund == 70

    def test_exact_usage(self, engine: CreditEngine) -> None:
        """预扣 = 实际 → 退还 0。"""
        refund = engine.calculate_refund(estimated=100, actual=100)
        assert refund == 0

    def test_actual_exceeds_estimated(self, engine: CreditEngine) -> None:
        """实际超出预扣时退还为 0（不能为负数）。"""
        refund = engine.calculate_refund(estimated=80, actual=150)
        assert refund == 0

    def test_zero_values(self, engine: CreditEngine) -> None:
        """双零情况。"""
        refund = engine.calculate_refund(estimated=0, actual=0)
        assert refund == 0


class TestValidateBalance:
    """测试余额校验。"""

    def test_sufficient_balance(self, engine: CreditEngine) -> None:
        """余额充足返回 True。"""
        assert engine.validate_balance(balance=500, required=100) is True

    def test_exact_balance(self, engine: CreditEngine) -> None:
        """余额恰好等于所需返回 True。"""
        assert engine.validate_balance(balance=100, required=100) is True

    def test_insufficient_balance(self, engine: CreditEngine) -> None:
        """余额不足返回 False。"""
        assert engine.validate_balance(balance=50, required=100) is False

    def test_zero_balance(self, engine: CreditEngine) -> None:
        """余额为 0 且需求 > 0 返回 False。"""
        assert engine.validate_balance(balance=0, required=1) is False

    def test_zero_required(self, engine: CreditEngine) -> None:
        """所需为 0 时总是 True。"""
        assert engine.validate_balance(balance=0, required=0) is True


class TestGetPricing:
    """测试定价查询。"""

    def test_get_tier_pricing(self, engine: CreditEngine) -> None:
        """获取 Speed 档位定价。"""
        pricing = engine.get_tier_pricing(ModelTier.SPEED)
        assert pricing.tier == ModelTier.SPEED
        assert pricing.credits_per_1k_tokens == 10

    def test_get_all_pricing(self, engine: CreditEngine) -> None:
        """获取所有档位定价。"""
        all_pricing = engine.get_all_pricing()
        assert all_pricing == {"speed": 10, "pro": 50, "elite": 150}
