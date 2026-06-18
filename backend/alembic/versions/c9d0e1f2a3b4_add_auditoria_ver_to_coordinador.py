"""add auditoria:ver with scope propio to COORDINADOR role

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-06-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO role_permissions (id, role_id, permission_id, scope, tenant_id)
        SELECT gen_random_uuid(), r.id, p.id, 'propio', r.tenant_id
        FROM roles r, permissions p
        WHERE r.name = 'COORDINADOR' AND p.name = 'auditoria:ver'
        AND NOT EXISTS (
            SELECT 1 FROM role_permissions rp
            WHERE rp.role_id = r.id AND rp.permission_id = p.id
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM role_permissions
        WHERE role_id IN (SELECT id FROM roles WHERE name = 'COORDINADOR')
        AND permission_id IN (SELECT id FROM permissions WHERE name = 'auditoria:ver')
        AND scope = 'propio'
        """
    )
