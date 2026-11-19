from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.core.security import decode_token
from app.db.base import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    MembershipResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        user, tenant, membership = await auth_service.register(db, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return auth_service.generate_tokens(user.id, tenant.id, membership.role.value)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await auth_service.authenticate(db, data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    memberships = await auth_service.get_user_memberships(db, user.id)
    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active organization membership",
        )

    if data.tenant_id is not None:
        membership = next(
            (m for m in memberships if m.tenant_id == data.tenant_id),
            None,
        )
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No membership in the specified organization",
            )
    else:
        membership = memberships[0]

    return auth_service.generate_tokens(user.id, membership.tenant_id, membership.role.value)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        payload = decode_token(data.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id_str = payload.get("sub")
    tenant_id_str = payload.get("tenant_id")
    role = payload.get("role")
    if not all([user_id_str, tenant_id_str, role]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        )

    import uuid

    user = await auth_service.get_user_by_id(db, uuid.UUID(user_id_str))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return auth_service.generate_tokens(
        uuid.UUID(user_id_str),
        uuid.UUID(tenant_id_str),
        role,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    _user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    return {"detail": "Successfully logged out"}


@router.get("/me", response_model=MeResponse)
async def get_me(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    memberships = await auth_service.get_user_memberships(db, user.id)
    return MeResponse(
        user=UserResponse.model_validate(user),
        memberships=[
            MembershipResponse(
                id=m.id,
                tenant_id=m.tenant_id,
                tenant_name=m.tenant.name,
                role=m.role.value,
            )
            for m in memberships
        ],
    )
