"""create audit_log table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("impersonado_id", sa.UUID(), nullable=True),
        sa.Column("materia_id", sa.UUID(), nullable=True),
        sa.Column("accion", sa.String(100), nullable=False),
        sa.Column("detalle", postgresql.JSON(), nullable=True),
        sa.Column("filas_afectadas", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["impersonado_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_tenant_fecha", "audit_log", ["tenant_id", "fecha_hora"])
    op.create_index("ix_audit_log_accion", "audit_log", ["accion"])
    op.create_index("ix_audit_log_actor_id", "audit_log", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_actor_id", table_name="audit_log")
    op.drop_index("ix_audit_log_accion", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_fecha", table_name="audit_log")
    op.drop_table("audit_log")
