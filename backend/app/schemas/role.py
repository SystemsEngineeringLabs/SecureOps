from pydantic import BaseModel


class PermissionResponse(BaseModel):
    resource: str
    action: str


class RoleResponse(BaseModel):
    name: str
    display_name: str
    permissions: list[PermissionResponse]


class RoleListResponse(BaseModel):
    roles: list[RoleResponse]
