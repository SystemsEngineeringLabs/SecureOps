import re
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.core.security import BCRYPT_MAX_PASSWORD_BYTES


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: uuid.UUID | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    tenant_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            raise ValueError(f"Password must be at most {BCRYPT_MAX_PASSWORD_BYTES} bytes")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 255:
            raise ValueError("Full name must be between 1 and 255 characters")
        return v

    @field_validator("tenant_name")
    @classmethod
    def validate_tenant_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 255:
            raise ValueError("Organization name must be between 2 and 255 characters")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth2 token type, not a secret


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    mfa_enabled: bool

    model_config = ConfigDict(from_attributes=True)


class MembershipResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    tenant_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class MeResponse(BaseModel):
    user: UserResponse
    memberships: list[MembershipResponse]
