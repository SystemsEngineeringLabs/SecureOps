import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.security import hash_password
from app.models.enums import MembershipRole


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def tenant_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def sample_tenant(tenant_id):
    tenant = MagicMock()
    tenant.id = tenant_id
    tenant.name = "Acme Security Corp"
    tenant.slug = "acme-security-corp"
    tenant.is_active = True
    tenant.settings = None
    tenant.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    tenant.updated_at = datetime(2024, 1, 15, tzinfo=UTC)
    return tenant


@pytest.fixture
def sample_user(user_id):
    user = MagicMock()
    user.id = user_id
    user.email = "admin@acmesecurity.com"
    user.hashed_password = hash_password("SecureP@ss1")
    user.full_name = "Jane Admin"
    user.is_active = True
    user.is_superuser = False
    user.mfa_enabled = False
    user.mfa_secret = None
    user.last_login_at = None
    user.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    user.updated_at = datetime(2024, 1, 15, tzinfo=UTC)
    return user


@pytest.fixture
def sample_membership(tenant_id, user_id):
    membership = MagicMock()
    membership.id = uuid.uuid4()
    membership.tenant_id = tenant_id
    membership.user_id = user_id
    membership.role = MembershipRole.ORG_ADMIN
    membership.is_active = True
    membership.invited_by = None
    membership.joined_at = datetime(2024, 1, 15, tzinfo=UTC)
    membership.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    membership.updated_at = datetime(2024, 1, 15, tzinfo=UTC)
    return membership


@pytest.fixture
def token_payload(user_id, tenant_id):
    return {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": MembershipRole.ORG_ADMIN.value,
        "type": "access",
    }
