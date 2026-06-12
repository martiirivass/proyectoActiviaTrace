"""create aviso and acknowledgment_aviso tables

Revision ID: 3c4d5e6f7a8b
Revises: 2b3c4d5e6f7a
Create Date: 2026-06-12 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "3c4d5e6f7a8b"
down_revision: Union[str, Sequence[str], None] = "2b3c4d5e6f7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Create enums ---
    sa.Enum("Global", "PorMateria", "PorCohorte", "PorRol", name="alcance_aviso").create(op.get_bind())
    sa.Enum("Info", "Advertencia", "Critico", name="severidad_aviso").create(op.get_bind())

    # --- avisos ---
    op.create_table(
        "avisos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False, index=True),
        sa.Column(
            "alcance",
            sa.Enum("Global", "PorMateria", "PorCohorte", "PorRol", name="alcance_aviso"),
            nullable=False,
        ),
        sa.Column("materia_id", sa.UUID(), nullable=True, index=True),
        sa.Column("cohorte_id", sa.UUID(), nullable=True, index=True),
        sa.Column("rol_destino", sa.String(length=50), nullable=True),
        sa.Column(
            "severidad",
            sa.Enum("Info", "Advertencia", "Critico", name="severidad_aviso"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("inicio_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requiere_ack", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_avisos_tenant_vigencia", "avisos", ["tenant_id", "inicio_en", "fin_en"])

    # --- acknowledgment_avisos ---
    op.create_table(
        "acknowledgment_avisos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False, index=True),
        sa.Column("aviso_id", sa.UUID(), nullable=False, index=True),
        sa.Column("usuario_id", sa.UUID(), nullable=False, index=True),
        sa.Column("confirmado_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aviso_id"], ["avisos.id"], ),
        sa.ForeignKeyConstraint(["usuario_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aviso_id", "usuario_id", name="uq_aviso_usuario_ack"),
    )


def downgrade() -> None:
    op.drop_table("acknowledgment_avisos")
    op.drop_table("avisos")

    sa.Enum(name="alcance_aviso").drop(op.get_bind())
    sa.Enum(name="severidad_aviso").drop(op.get_bind())
