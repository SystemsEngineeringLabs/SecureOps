from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_active_user
from app.core.permissions import ROLE_DISPLAY_NAMES, ROLE_PERMISSIONS
from app.models.enums import MembershipRole
from app.models.user import User
from app.schemas.role import PermissionResponse, RoleListResponse, RoleResponse

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=RoleListResponse)
async def list_roles(
    _user: User = Depends(get_current_active_user),
) -> RoleListResponse:
    roles = []
    for member_role in MembershipRole:
        perms = ROLE_PERMISSIONS.get(member_role, set())
        roles.append(
            RoleResponse(
                name=member_role.value,
                display_name=ROLE_DISPLAY_NAMES.get(member_role, member_role.value),
                permissions=[
                    PermissionResponse(resource=r, action=a)
                    for r, a in sorted(perms)
                ],
            )
        )
    return RoleListResponse(roles=roles)


@router.get("/{role_name}/permissions", response_model=list[PermissionResponse])
async def get_role_permissions(
    role_name: str,
    _user: User = Depends(get_current_active_user),
) -> list[PermissionResponse]:
    try:
        member_role = MembershipRole(role_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found",
        )

    perms = ROLE_PERMISSIONS.get(member_role, set())
    return [PermissionResponse(resource=r, action=a) for r, a in sorted(perms)]
