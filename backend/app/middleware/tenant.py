from uuid import UUID

from fastapi import Request, Response
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings
from app.core.tenant_context import clear_tenant, set_tenant

PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/api/v1/docs",
        "/api/v1/openapi.json",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    }
)

PUBLIC_PREFIXES = (
    "/api/v1/docs",
    "/api/v1/redoc",
)


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        try:
            tenant_id = self._extract_tenant_from_token(request)
            if tenant_id is not None:
                set_tenant(tenant_id)
            return await call_next(request)
        finally:
            clear_tenant()

    @staticmethod
    def _extract_tenant_from_token(request: Request) -> UUID | None:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.removeprefix("Bearer ")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            tenant_id_str = payload.get("tenant_id")
            if tenant_id_str:
                return UUID(tenant_id_str)
        except (JWTError, ValueError):
            pass
        return None
