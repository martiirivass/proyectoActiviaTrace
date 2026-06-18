"""add sexo to users, create mensajes table

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-06-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Add sexo column to users ---
    op.add_column(
        "users",
        sa.Column("sexo", sa.String(50), nullable=True),
    )

    # --- Create mensajes table ---
    op.create_table(
        "mensajes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("hilo_id", sa.UUID(), nullable=False),
        sa.Column("remitente_id", sa.UUID(), nullable=False),
        sa.Column("destinatario_id", sa.UUID(), nullable=False),
        sa.Column("asunto", sa.String(200), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("leido", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.ForeignKeyConstraint(["remitente_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["destinatario_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mensajes_tenant_id"), "mensajes", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_mensajes_hilo_id"), "mensajes", ["hilo_id"], unique=False)
    op.create_index(op.f("ix_mensajes_remitente_id"), "mensajes", ["remitente_id"], unique=False)
    op.create_index(op.f("ix_mensajes_destinatario_id"), "mensajes", ["destinatario_id"], unique=False)


def downgrade() -> None:
    op.drop_table("mensajes")
    op.drop_column("users", "sexo")
