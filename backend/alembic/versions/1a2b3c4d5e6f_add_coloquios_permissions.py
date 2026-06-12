"""add coloquios permissions (gestionar + reservar) and assign to roles

Revision ID: 1a2b3c4d5e6f
Revises: 0a1b2c3d4e5f
Create Date: 2026-06-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "0a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    permissions_table = sa.table(
        "permissions",
        sa.Column("id", sa.UUID()),
        sa.Column("name", sa.String()),
        sa.Column("module", sa.String()),
        sa.Column("action", sa.String()),
        sa.Column("description", sa.String()),
    )

    roles_table = sa.table(
        "roles",
        sa.Column("id", sa.UUID()),
        sa.Column("name", sa.String()),
    )

    role_permissions_table = sa.table(
        "role_permissions",
        sa.Column("id", sa.UUID()),
        sa.Column("role_id", sa.UUID()),
        sa.Column("permission_id", sa.UUID()),
        sa.Column("scope", sa.String()),
        sa.Column("tenant_id", sa.UUID()),
    )

    import uuid

    # Get default tenant from first existing tenant
    result = conn.execute(sa.text("SELECT id FROM tenants LIMIT 1"))
    row = result.fetchone()
    if not row:
        default_tenant_id = uuid.uuid4()
        op.execute(
            sa.insert(sa.table(
                "tenants",
                sa.Column("id", sa.UUID()),
                sa.Column("name", sa.String()),
                sa.Column("code", sa.String()),
                sa.Column("is_active", sa.Boolean()),
            )).values(
                id=default_tenant_id,
                name="System",
                code="SYS",
                is_active=True,
            )
        )
    else:
        default_tenant_id = row[0]

    # --- Insert new permissions ---
    new_permissions = [
        {
            "name": "coloquios:gestionar",
            "module": "coloquios",
            "action": "gestionar",
            "description": "Gestionar evaluaciones y coloquios",
        },
        {
            "name": "coloquios:reservar",
            "module": "coloquios",
            "action": "reservar",
            "description": "Reservar turno de coloquio",
        },
    ]

    permission_ids = {}
    for p in new_permissions:
        pid = uuid.uuid4()
        permission_ids[p["name"]] = pid
        op.execute(
            sa.insert(permissions_table).values(
                id=pid,
                name=p["name"],
                module=p["module"],
                action=p["action"],
                description=p["description"],
            )
        )

    # --- Get role IDs ---
    result = conn.execute(sa.text("SELECT id, name FROM roles"))
    roles = {row[1]: row[0] for row in result.fetchall()}

    # --- Assign coloquios:gestionar to PROFESOR, COORDINADOR, ADMIN, NEXO ---
    gestionar_roles = ["PROFESOR", "COORDINADOR", "ADMIN", "NEXO"]
    for role_name in gestionar_roles:
        if role_name in roles:
            rpid = uuid.uuid4()
            op.execute(
                sa.insert(role_permissions_table).values(
                    id=rpid,
                    role_id=roles[role_name],
                    permission_id=permission_ids["coloquios:gestionar"],
                    scope="global",
                    tenant_id=default_tenant_id,
                )
            )

    # --- Assign coloquios:reservar to ALUMNO ---
    if "ALUMNO" in roles:
        rpid = uuid.uuid4()
        op.execute(
            sa.insert(role_permissions_table).values(
                id=rpid,
                role_id=roles["ALUMNO"],
                permission_id=permission_ids["coloquios:reservar"],
                scope="global",
                tenant_id=default_tenant_id,
            )
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Delete role_permissions for these permissions
    perm_names = ("coloquios:gestionar", "coloquios:reservar")
    conn.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN "
            "(SELECT id FROM permissions WHERE name = ANY(:names))"
        ),
        {"names": list(perm_names)},
    )

    # Delete the permissions themselves
    conn.execute(
        sa.text("DELETE FROM permissions WHERE name = ANY(:names)"),
        {"names": list(perm_names)},
    )
