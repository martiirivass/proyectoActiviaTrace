"""create comunicacion and lote_comunicacion tables

Revision ID: d5e6f7a8b9c0
Revises: 0a1b2c3d4e5f
Create Date: 2026-06-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "0a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Create enum types ---
    op.execute("CREATE TYPE estado_comunicacion AS ENUM ('Pendiente', 'Enviando', 'Enviado', 'Error', 'Cancelado')")
    op.execute("CREATE TYPE estado_lote AS ENUM ('Pendiente', 'Aprobado', 'Rechazado')")

    # --- Table: lote_comunicacion ---
    op.create_table(
        "lote_comunicacion",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("materia_id", sa.UUID(), nullable=False),
        sa.Column("enviado_por", sa.UUID(), nullable=False),
        sa.Column("total_mensajes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "estado",
            postgresql.ENUM("Pendiente", "Aprobado", "Rechazado", name="estado_lote", create_type=False),
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column("aprobado_por", sa.UUID(), nullable=True),
        sa.Column("aprobado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rechazado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.ForeignKeyConstraint(["enviado_por"], ["users.id"], ),
        sa.ForeignKeyConstraint(["aprobado_por"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lote_comunicacion_tenant_id"), "lote_comunicacion", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_lote_comunicacion_materia_id"), "lote_comunicacion", ["materia_id"], unique=False)
    op.create_index(op.f("ix_lote_comunicacion_enviado_por"), "lote_comunicacion", ["enviado_por"], unique=False)
    op.create_index(
        "ix_lote_comunicacion_tenant_estado",
        "lote_comunicacion",
        ["tenant_id", "estado"],
        unique=False,
    )

    # --- Table: comunicacion ---
    op.create_table(
        "comunicacion",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("lote_id", sa.UUID(), nullable=True),
        sa.Column("enviado_por", sa.UUID(), nullable=False),
        sa.Column("materia_id", sa.UUID(), nullable=False),
        sa.Column("destinatario", sa.String(500), nullable=False),
        sa.Column("asunto", sa.String(255), nullable=False),
        sa.Column("cuerpo", sa.String(5000), nullable=False),
        sa.Column(
            "estado",
            postgresql.ENUM("Pendiente", "Enviando", "Enviado", "Error", "Cancelado", name="estado_comunicacion", create_type=False),
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column("error_msg", sa.String(1000), nullable=True),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lote_id"], ["lote_comunicacion.id"], ),
        sa.ForeignKeyConstraint(["enviado_por"], ["users.id"], ),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comunicacion_tenant_id"), "comunicacion", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_comunicacion_lote_id"), "comunicacion", ["lote_id"], unique=False)
    op.create_index(op.f("ix_comunicacion_enviado_por"), "comunicacion", ["enviado_por"], unique=False)
    op.create_index(op.f("ix_comunicacion_materia_id"), "comunicacion", ["materia_id"], unique=False)
    op.create_index(
        "ix_comunicacion_tenant_lote",
        "comunicacion",
        ["tenant_id", "lote_id"],
        unique=False,
    )
    op.create_index(
        "ix_comunicacion_tenant_materia_estado",
        "comunicacion",
        ["tenant_id", "materia_id", "estado"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("comunicacion")
    op.drop_table("lote_comunicacion")
    op.execute("DROP TYPE IF EXISTS estado_comunicacion")
    op.execute("DROP TYPE IF EXISTS estado_lote")
