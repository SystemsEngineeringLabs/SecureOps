from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_tenant_membership
from app.core.permissions import ROLE_PERMISSIONS
from app.models.enums import MembershipRole
from app.models.membership import Membership
from app.models.user import User


def require_permission(resource: str, action: str) -> Callable[..., Any]:
    """FastAPI dependency that checks if the current user's role grants (resource, action)."""

    async def _check(
        user_and_membership: tuple[User, Membership] = Depends(get_current_tenant_membership),
    ) -> tuple[User, Membership]:
        user, membership = user_and_membership
        allowed = ROLE_PERMISSIONS.get(membership.role, set())
        if (resource, action) not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires {resource}:{action}",
            )
        return user, membership

    return _check


def require_any_permission(*permissions: tuple[str, str]) -> Callable[..., Any]:
    """FastAPI dependency that requires at least one of the given permissions."""

    async def _check(
        user_and_membership: tuple[User, Membership] = Depends(get_current_tenant_membership),
    ) -> tuple[User, Membership]:
        user, membership = user_and_membership
        allowed = ROLE_PERMISSIONS.get(membership.role, set())
        if not any(perm in allowed for perm in permissions):
            labels = ", ".join(f"{r}:{a}" for r, a in permissions)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires one of [{labels}]",
            )
        return user, membership

    return _check


def require_role(*roles: MembershipRole) -> Callable[..., Any]:
    """FastAPI dependency that requires the user to have one of the specified roles."""

    async def _check(
        user_and_membership: tuple[User, Membership] = Depends(get_current_tenant_membership),
    ) -> tuple[User, Membership]:
        user, membership = user_and_membership
        if membership.role not in roles:
            role_names = ", ".join(r.value for r in roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires role [{role_names}]",
            )
        return user, membership

    return _check
