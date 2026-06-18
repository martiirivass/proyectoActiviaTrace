"""create aviso and acknowledgment_aviso tables

Revision ID: f7a8b9c0d1e2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Create enum types ---
    op.execute("CREATE TYPE alcance_aviso AS ENUM ('Global', 'PorMateria', 'PorCohorte', 'PorRol')")
    op.execute("CREATE TYPE severidad_aviso AS ENUM ('Info', 'Advertencia', 'Critico')")

    # --- Table: avisos ---
    op.create_table(
        "avisos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column(
            "alcance",
            postgresql.ENUM("Global", "PorMateria", "PorCohorte", "PorRol", name="alcance_aviso", create_type=False),
            nullable=False,
        ),
        sa.Column("materia_id", sa.UUID(), nullable=True),
        sa.Column("cohorte_id", sa.UUID(), nullable=True),
        sa.Column("rol_destino", sa.String(50), nullable=True),
        sa.Column(
            "severidad",
            postgresql.ENUM("Info", "Advertencia", "Critico", name="severidad_aviso", create_type=False),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(255), nullable=False),
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
    op.create_index(op.f("ix_avisos_tenant_id"), "avisos", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_avisos_materia_id"), "avisos", ["materia_id"], unique=False)
    op.create_index(op.f("ix_avisos_cohorte_id"), "avisos", ["cohorte_id"], unique=False)
    # Composite index for active + vigencia queries
    op.create_index("ix_avisos_tenant_activo_vigencia", "avisos", ["tenant_id", "activo", "inicio_en", "fin_en"], unique=False)

    # --- Table: acknowledgment_aviso ---
    op.create_table(
        "acknowledgment_aviso",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("aviso_id", sa.UUID(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("confirmado_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["aviso_id"], ["avisos.id"], ),
        sa.ForeignKeyConstraint(["usuario_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aviso_id", "usuario_id", name="uq_aviso_usuario_ack"),
    )
    op.create_index(op.f("ix_acknowledgment_aviso_aviso_id"), "acknowledgment_aviso", ["aviso_id"], unique=False)
    op.create_index(op.f("ix_acknowledgment_aviso_usuario_id"), "acknowledgment_aviso", ["usuario_id"], unique=False)


def downgrade() -> None:
    op.drop_table("acknowledgment_aviso")
    op.drop_table("avisos")
    op.execute("DROP TYPE IF EXISTS alcance_aviso")
    op.execute("DROP TYPE IF EXISTS severidad_aviso")
