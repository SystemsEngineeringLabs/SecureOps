import uuid
from datetime import timedelta

import pytest
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

pytestmark = pytest.mark.unit


class TestPasswordHashing:
    def test_hash_password_produces_bcrypt_hash(self):
        hashed = hash_password("MySecureP@ss1")
        assert hashed.startswith(("$2b$", "$2a$"))

    def test_hash_password_different_each_call(self):
        h1 = hash_password("SamePassword1!")
        h2 = hash_password("SamePassword1!")
        assert h1 != h2

    def test_verify_password_correct(self):
        hashed = hash_password("CorrectP@ss1")
        assert verify_password("CorrectP@ss1", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("CorrectP@ss1")
        assert verify_password("WrongPassword!", hashed) is False

    def test_verify_password_empty_string(self):
        hashed = hash_password("RealP@ssw0rd")
        assert verify_password("", hashed) is False

    def test_hash_rejects_password_over_bcrypt_limit(self):
        # bcrypt only uses the first 72 bytes; never silently truncate
        with pytest.raises(ValueError, match="72"):
            hash_password("A1!" + "a" * 70)

    def test_hash_limit_counts_bytes_not_characters(self):
        with pytest.raises(ValueError, match="72"):
            hash_password("é" * 37)  # 37 chars, 74 bytes

    def test_hash_accepts_exactly_72_bytes(self):
        pw = "A1!" + "a" * 69
        assert verify_password(pw, hash_password(pw)) is True

    def test_verify_over_limit_returns_false(self):
        pw = "A1!" + "a" * 69
        assert verify_password(pw + "extra", hash_password(pw)) is False

    @pytest.mark.parametrize("bad_hash", ["PENDING_REGISTRATION", "", "$2b$garbage"])
    def test_verify_malformed_hash_returns_false(self, bad_hash):
        assert verify_password("Whatever1!", bad_hash) is False


class TestAccessToken:
    def test_create_access_token_returns_string(self, token_payload):
        token = create_access_token(token_payload)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_expected_claims(self, token_payload):
        token = create_access_token(token_payload)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == token_payload["sub"]
        assert decoded["tenant_id"] == token_payload["tenant_id"]
        assert decoded["role"] == token_payload["role"]
        assert decoded["type"] == "access"
        assert "exp" in decoded

    def test_access_token_custom_expiry(self, token_payload):
        token = create_access_token(token_payload, expires_delta=timedelta(minutes=5))
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["type"] == "access"

    def test_access_token_default_expiry(self, token_payload):
        token = create_access_token(token_payload)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in decoded


class TestRefreshToken:
    def test_create_refresh_token_returns_string(self, token_payload):
        token = create_refresh_token(token_payload)
        assert isinstance(token, str)

    def test_refresh_token_type_is_refresh(self, token_payload):
        token = create_refresh_token(token_payload)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["type"] == "refresh"

    def test_refresh_token_contains_subject(self, token_payload):
        token = create_refresh_token(token_payload)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == token_payload["sub"]


class TestDecodeToken:
    def test_decode_valid_token(self, token_payload):
        token = create_access_token(token_payload)
        decoded = decode_token(token)
        assert decoded["sub"] == token_payload["sub"]
        assert decoded["type"] == "access"

    def test_decode_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_token("not.a.valid.token")

    def test_decode_wrong_secret_raises(self, token_payload):
        token = jwt.encode(token_payload, "wrong-secret", algorithm=settings.ALGORITHM)
        with pytest.raises(JWTError):
            decode_token(token)

    def test_decode_expired_token_raises(self):
        payload = {"sub": str(uuid.uuid4()), "type": "access"}
        token = jwt.encode(
            {**payload, "exp": 0},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        with pytest.raises(JWTError):
            decode_token(token)
