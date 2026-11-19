import uuid
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

pytestmark = pytest.mark.unit


class TestLoginRequest:
    def test_valid_login(self):
        req = LoginRequest(email="user@example.com", password="LongEnough1!")
        assert req.email == "user@example.com"
        assert req.password == "LongEnough1!"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="LongEnough1!")

    def test_optional_tenant_id(self):
        tid = uuid.uuid4()
        req = LoginRequest(email="u@e.com", password="LongEnough1!", tenant_id=tid)
        assert req.tenant_id == tid

    def test_tenant_id_defaults_none(self):
        req = LoginRequest(email="u@e.com", password="LongEnough1!")
        assert req.tenant_id is None


class TestRegisterRequest:
    VALID = {
        "email": "admin@example.com",
        "password": "SecureP@ss1",
        "full_name": "Jane Doe",
        "tenant_name": "Acme Corp",
    }

    def test_valid_registration(self):
        req = RegisterRequest(**self.VALID)
        assert req.email == "admin@example.com"
        assert req.full_name == "Jane Doe"

    def test_password_too_short(self):
        with pytest.raises(ValidationError, match="at least 8"):
            RegisterRequest(**{**self.VALID, "password": "Sh0rt!"})

    def test_password_no_uppercase(self):
        with pytest.raises(ValidationError, match="uppercase"):
            RegisterRequest(**{**self.VALID, "password": "noupperc@se1"})

    def test_password_no_lowercase(self):
        with pytest.raises(ValidationError, match="lowercase"):
            RegisterRequest(**{**self.VALID, "password": "NOLOWERC@SE1"})

    def test_password_no_digit(self):
        with pytest.raises(ValidationError, match="digit"):
            RegisterRequest(**{**self.VALID, "password": "NoDigit@Here"})

    def test_password_no_special_char(self):
        with pytest.raises(ValidationError, match="special"):
            RegisterRequest(**{**self.VALID, "password": "NoSpecial1Ab"})

    def test_password_max_length(self):
        with pytest.raises(ValidationError, match="at most 72 bytes"):
            RegisterRequest(**{**self.VALID, "password": "A@1a" + "x" * 69})

    def test_password_max_length_counts_utf8_bytes(self):
        # 40 characters but 76 bytes in UTF-8
        with pytest.raises(ValidationError, match="at most 72 bytes"):
            RegisterRequest(**{**self.VALID, "password": "A@1a" + "é" * 36})

    def test_password_exactly_72_bytes_accepted(self):
        pw = "A@1a" + "x" * 68
        assert RegisterRequest(**{**self.VALID, "password": pw}).password == pw

    def test_empty_tenant_name_rejected(self):
        with pytest.raises(ValidationError, match="Organization name"):
            RegisterRequest(**{**self.VALID, "tenant_name": "a"})

    def test_tenant_name_stripped(self):
        req = RegisterRequest(**{**self.VALID, "tenant_name": "  Acme Corp  "})
        assert req.tenant_name == "Acme Corp"

    def test_full_name_stripped(self):
        req = RegisterRequest(**{**self.VALID, "full_name": "  Jane  "})
        assert req.full_name == "Jane"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**{**self.VALID, "email": "bad"})


class TestTokenResponse:
    def test_serialization(self):
        resp = TokenResponse(
            access_token="acc.tok.en",
            refresh_token="ref.tok.en",
        )
        assert resp.token_type == "bearer"
        data = resp.model_dump()
        assert data["access_token"] == "acc.tok.en"
        assert data["refresh_token"] == "ref.tok.en"
        assert data["token_type"] == "bearer"


class TestUserResponse:
    def test_from_attributes(self):
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.email = "u@e.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        mock_user.mfa_enabled = False

        resp = UserResponse.model_validate(mock_user, from_attributes=True)
        assert resp.email == "u@e.com"
        assert resp.full_name == "Test User"
        assert resp.is_active is True

    def test_serialization_round_trip(self):
        uid = uuid.uuid4()
        resp = UserResponse(
            id=uid,
            email="x@y.com",
            full_name="X Y",
            is_active=True,
            mfa_enabled=False,
        )
        data = resp.model_dump()
        restored = UserResponse(**data)
        assert restored.id == uid
