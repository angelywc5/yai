"""安全工具单元测试。"""

import pytest

from src.core.exceptions import TokenExpiredError, TokenInvalidError
from src.utils.security import JwtTokenManager, PasswordHasher


# ============================================================================
# PasswordHasher 测试
# ============================================================================


class TestPasswordHasher:
    """测试密码哈希与验证。"""

    def test_hash_and_verify_success(self) -> None:
        """bcrypt 哈希与校验。"""
        password = "mySecurePassword123"
        hashed = PasswordHasher.hash_password(password)
        assert PasswordHasher.verify_password(password, hashed) is True

    def test_hash_not_plaintext(self) -> None:
        """哈希结果不等于明文。"""
        password = "testPassword"
        hashed = PasswordHasher.hash_password(password)
        assert hashed != password

    def test_verify_wrong_password(self) -> None:
        """错误密码校验失败。"""
        hashed = PasswordHasher.hash_password("correctPassword")
        assert PasswordHasher.verify_password("wrongPassword", hashed) is False

    def test_hash_different_each_time(self) -> None:
        """相同密码每次哈希结果不同（自动加盐）。"""
        password = "samePassword"
        hash1 = PasswordHasher.hash_password(password)
        hash2 = PasswordHasher.hash_password(password)
        assert hash1 != hash2
        # 但两个哈希都能验证通过
        assert PasswordHasher.verify_password(password, hash1) is True
        assert PasswordHasher.verify_password(password, hash2) is True

    def test_verify_invalid_hash_returns_false(self) -> None:
        """无效哈希字符串不会崩溃，返回 False。"""
        result = PasswordHasher.verify_password("password", "not-a-valid-hash")
        assert result is False

    def test_unicode_password(self) -> None:
        """支持 Unicode 密码。"""
        password = "密码测试🔐"
        hashed = PasswordHasher.hash_password(password)
        assert PasswordHasher.verify_password(password, hashed) is True


# ============================================================================
# JwtTokenManager 测试
# ============================================================================


class TestJwtTokenManager:
    """测试 JWT 令牌管理。"""

    @pytest.fixture
    def jwt_manager(self) -> JwtTokenManager:
        """创建 JWT 管理器。"""
        return JwtTokenManager(secret_key="test-secret-key", algorithm="HS256")

    def test_create_and_decode_access_token(
        self, jwt_manager: JwtTokenManager
    ) -> None:
        """JWT 生成与解码。"""
        token = jwt_manager.create_access_token(user_id="user123", expires_minutes=60)
        payload = jwt_manager.decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(
        self, jwt_manager: JwtTokenManager
    ) -> None:
        """Refresh Token 生成与解码。"""
        token = jwt_manager.create_refresh_token(user_id="user456", expires_minutes=60)
        payload = jwt_manager.decode_token(token)
        assert payload["sub"] == "user456"
        assert payload["type"] == "refresh"

    def test_payload_contains_sub_and_type(
        self, jwt_manager: JwtTokenManager
    ) -> None:
        """Payload 包含 sub 和 type。"""
        token = jwt_manager.create_access_token(user_id="user789", expires_minutes=60)
        payload = jwt_manager.decode_token(token)
        assert "sub" in payload
        assert "type" in payload
        assert "exp" in payload
        assert "iat" in payload

    def test_expired_token_raises(self, jwt_manager: JwtTokenManager) -> None:
        """过期 JWT 抛出 TokenExpiredError。"""
        from datetime import datetime, timedelta, timezone
        from jose import jwt as jose_jwt

        # 手动构建一个已过期的 token
        expire = datetime.now(timezone.utc) - timedelta(seconds=10)
        payload = {
            "sub": "user123",
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        expired_token = jose_jwt.encode(
            payload, jwt_manager.secret_key, algorithm=jwt_manager.algorithm
        )
        with pytest.raises(TokenExpiredError):
            jwt_manager.decode_token(expired_token)

    def test_invalid_signature_raises(self, jwt_manager: JwtTokenManager) -> None:
        """篡改签名抛出 TokenInvalidError。"""
        token = jwt_manager.create_access_token(user_id="user123", expires_minutes=60)
        # 篡改 token 的最后几个字符
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(TokenInvalidError):
            jwt_manager.decode_token(tampered)

    def test_wrong_secret_key_raises(self, jwt_manager: JwtTokenManager) -> None:
        """使用不同密钥解码抛出异常。"""
        token = jwt_manager.create_access_token(user_id="user123", expires_minutes=60)
        other_manager = JwtTokenManager(
            secret_key="different-secret-key", algorithm="HS256"
        )
        with pytest.raises(TokenInvalidError):
            other_manager.decode_token(token)

    def test_token_type_validation_access(
        self, jwt_manager: JwtTokenManager
    ) -> None:
        """校验 token_type 为 access 时通过。"""
        token = jwt_manager.create_access_token(user_id="user123", expires_minutes=60)
        payload = jwt_manager.decode_token(token, token_type="access")
        assert payload["type"] == "access"

    def test_token_type_validation_mismatch(
        self, jwt_manager: JwtTokenManager
    ) -> None:
        """token_type 不匹配时抛出 TokenInvalidError。"""
        token = jwt_manager.create_access_token(user_id="user123", expires_minutes=60)
        with pytest.raises(TokenInvalidError):
            jwt_manager.decode_token(token, token_type="refresh")

    def test_completely_invalid_token(self, jwt_manager: JwtTokenManager) -> None:
        """完全无效的字符串抛出 TokenInvalidError。"""
        with pytest.raises(TokenInvalidError):
            jwt_manager.decode_token("this.is.not.a.valid.jwt")

    def test_empty_token(self, jwt_manager: JwtTokenManager) -> None:
        """空字符串抛出 TokenInvalidError。"""
        with pytest.raises(TokenInvalidError):
            jwt_manager.decode_token("")
