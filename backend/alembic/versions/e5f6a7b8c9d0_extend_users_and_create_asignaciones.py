"""extend users and create asignaciones

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-10 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to users
    op.add_column("users", sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id"), nullable=True))
    op.add_column("users", sa.Column("dni", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("cuil", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("cbu", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("alias_cbu", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("banco", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("regional", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("legajo_profesional", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("facturador", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("users", sa.Column("estado", sa.String(50), server_default=sa.text("'Activo'"), nullable=False))

    # Make legajo nullable
    op.alter_column("users", "legajo", nullable=True, type_=sa.String(50))

    # Drop global unique on email, create composite unique index instead
    op.drop_index("ix_users_email", table_name="users")
    op.create_index("ix_users_email_tenant", "users", ["email", "tenant_id"], unique=True)
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    # Create asignaciones table
    op.create_table(
        "asignaciones",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("materia_id", sa.UUID(), nullable=True),
        sa.Column("carrera_id", sa.UUID(), nullable=True),
        sa.Column("cohorte_id", sa.UUID(), nullable=True),
        sa.Column("dictado_id", sa.UUID(), nullable=True),
        sa.Column("comisiones", postgresql.JSON(), nullable=True),
        sa.Column("responsable_id", sa.UUID(), nullable=True),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"], ),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"], ),
        sa.ForeignKeyConstraint(["dictado_id"], ["dictados.id"], ),
        sa.ForeignKeyConstraint(["responsable_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_asignaciones_tenant_id", "asignaciones", ["tenant_id"])
    op.create_index("ix_asignaciones_usuario_id", "asignaciones", ["usuario_id"])

    # Permissions and role assignments are already seeded in C-04 migration.
    # No need to re-insert them here.


def downgrade() -> None:
    op.drop_table("asignaciones")
    op.drop_index("ix_users_email_tenant")
    op.drop_index("ix_users_tenant_id")
    op.create_unique_constraint("users_email_key", "users", ["email"])
    op.drop_column("users", "tenant_id")
    op.drop_column("users", "dni")
    op.drop_column("users", "cuil")
    op.drop_column("users", "cbu")
    op.drop_column("users", "alias_cbu")
    op.drop_column("users", "banco")
    op.drop_column("users", "regional")
    op.drop_column("users", "legajo_profesional")
    op.drop_column("users", "facturador")
    op.drop_column("users", "estado")
