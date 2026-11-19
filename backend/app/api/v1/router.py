from fastapi import APIRouter

from app.api.v1.endpoints import audit, auth, roles, tenants

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tenants.router)
api_router.include_router(audit.router)
api_router.include_router(roles.router)
