"""create estructura academica tables (carreras, cohortes, materias, dictados)

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-06-10 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "carreras",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("estado", sa.String(10), nullable=False, server_default=sa.text("'Activa'")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_carrera_tenant_codigo"),
    )
    op.create_index(op.f("ix_carreras_tenant_id"), "carreras", ["tenant_id"], unique=False)

    op.create_table(
        "cohortes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("carrera_id", sa.UUID(), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("vig_desde", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vig_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(10), nullable=False, server_default=sa.text("'Activa'")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "carrera_id", "nombre", name="uq_cohorte_tenant_carrera_nombre"),
    )
    op.create_index(op.f("ix_cohortes_tenant_id"), "cohortes", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_cohortes_carrera_id"), "cohortes", ["carrera_id"], unique=False)

    op.create_table(
        "materias",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("estado", sa.String(10), nullable=False, server_default=sa.text("'Activa'")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_materia_tenant_codigo"),
    )
    op.create_index(op.f("ix_materias_tenant_id"), "materias", ["tenant_id"], unique=False)

    op.create_table(
        "dictados",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("materia_id", sa.UUID(), nullable=False),
        sa.Column("carrera_id", sa.UUID(), nullable=False),
        sa.Column("cohorte_id", sa.UUID(), nullable=False),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"], ),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "materia_id", "cohorte_id", name="uq_dictado_tenant_materia_cohorte"),
    )
    op.create_index(op.f("ix_dictados_tenant_id"), "dictados", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_dictados_materia_id"), "dictados", ["materia_id"], unique=False)
    op.create_index(op.f("ix_dictados_carrera_id"), "dictados", ["carrera_id"], unique=False)
    op.create_index(op.f("ix_dictados_cohorte_id"), "dictados", ["cohorte_id"], unique=False)


def downgrade() -> None:
    op.drop_table("dictados")
    op.drop_table("materias")
    op.drop_table("cohortes")
    op.drop_table("carreras")
