from fastapi import APIRouter

from app.api.v1.endpoints import (
    audit,
    auth,
    compliance,
    evidence,
    policies,
    risks,
    roles,
    tenants,
    vendors,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tenants.router)
api_router.include_router(audit.router)
api_router.include_router(roles.router)
api_router.include_router(compliance.router)
api_router.include_router(risks.router)
api_router.include_router(evidence.router)
api_router.include_router(policies.router)
api_router.include_router(vendors.router)
