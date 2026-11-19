from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import ALL_ACTIONS, ALL_RESOURCES, ROLE_DISPLAY_NAMES, ROLE_PERMISSIONS
from app.models.enums import MembershipRole
from app.models.role import Permission, Role, RolePermission


def check_permission(role: MembershipRole, resource: str, action: str) -> bool:
    allowed = ROLE_PERMISSIONS.get(role, set())
    return (resource, action) in allowed


def get_role_permissions(role: MembershipRole) -> list[tuple[str, str]]:
    return sorted(ROLE_PERMISSIONS.get(role, set()))


async def seed_roles_and_permissions(db: AsyncSession) -> None:
    """Seed the database with system roles and permissions. Idempotent."""
    existing_perms_result = await db.execute(select(Permission))
    existing_perms = {(p.resource, p.action): p for p in existing_perms_result.scalars().all()}

    perm_objects: dict[tuple[str, str], Permission] = {}
    for resource in ALL_RESOURCES:
        for action in ALL_ACTIONS:
            key = (resource, action)
            if key in existing_perms:
                perm_objects[key] = existing_perms[key]
            else:
                perm = Permission(
                    resource=resource,
                    action=action,
                    description=f"{action} access to {resource}",
                )
                db.add(perm)
                perm_objects[key] = perm

    await db.flush()

    existing_roles_result = await db.execute(select(Role))
    existing_roles = {r.name: r for r in existing_roles_result.scalars().all()}

    for member_role in MembershipRole:
        role_name = member_role.value
        display_name = ROLE_DISPLAY_NAMES.get(member_role, role_name)

        if role_name in existing_roles:
            role = existing_roles[role_name]
            role.display_name = display_name
        else:
            role = Role(
                name=role_name,
                display_name=display_name,
                description=f"System role: {display_name}",
                is_system=True,
            )
            db.add(role)
            await db.flush()

        existing_rp_result = await db.execute(
            select(RolePermission).where(RolePermission.role_id == role.id)
        )
        existing_rp_perm_ids = {rp.permission_id for rp in existing_rp_result.scalars().all()}

        role_perms = ROLE_PERMISSIONS.get(member_role, set())
        for perm_key in role_perms:
            granted = perm_objects.get(perm_key)
            if granted and granted.id not in existing_rp_perm_ids:
                db.add(RolePermission(role_id=role.id, permission_id=granted.id))

    await db.commit()
