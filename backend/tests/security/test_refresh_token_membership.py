"""Token refresh must re-check live membership, not trust claims in the old token."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from jose import jwt

from app.api.v1.endpoints import auth as auth_endpoint
from app.core.config import settings
from app.core.security import create_refresh_token
from app.models.enums import MembershipRole
from app.schemas.auth import RefreshRequest

pytestmark = pytest.mark.security


@pytest.fixture
def ids():
    return uuid.uuid4(), uuid.uuid4()


def _refresh(user_id, tenant_id, role="admin"):
    return RefreshRequest(
        refresh_token=create_refresh_token(
            {"sub": str(user_id), "tenant_id": str(tenant_id), "role": role}
        )
    )


@pytest.fixture
def patch_service(monkeypatch):
    def _apply(user, membership):
        monkeypatch.setattr(
            auth_endpoint.auth_service, "get_user_by_id", AsyncMock(return_value=user)
        )
        monkeypatch.setattr(
            auth_endpoint.auth_service, "get_membership", AsyncMock(return_value=membership)
        )

    return _apply


async def test_refresh_denied_when_membership_removed(ids, patch_service):
    user_id, tenant_id = ids
    patch_service(SimpleNamespace(id=user_id, is_active=True), None)
    with pytest.raises(HTTPException) as exc:
        await auth_endpoint.refresh_token(_refresh(user_id, tenant_id), db=AsyncMock())
    assert exc.value.status_code == 401


async def test_refresh_uses_current_role_not_token_role(ids, patch_service):
    user_id, tenant_id = ids
    patch_service(
        SimpleNamespace(id=user_id, is_active=True),
        SimpleNamespace(role=MembershipRole.AUDITOR),
    )
    tokens = await auth_endpoint.refresh_token(
        _refresh(user_id, tenant_id, role="owner"), db=AsyncMock()
    )
    claims = jwt.decode(tokens.access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert claims["role"] == MembershipRole.AUDITOR.value


async def test_refresh_denied_for_inactive_user(ids, patch_service):
    user_id, tenant_id = ids
    patch_service(SimpleNamespace(id=user_id, is_active=False), SimpleNamespace(role="admin"))
    with pytest.raises(HTTPException) as exc:
        await auth_endpoint.refresh_token(_refresh(user_id, tenant_id), db=AsyncMock())
    assert exc.value.status_code == 401
