"""create liquidaciones, salarios_base, salarios_plus, facturas tables

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-06-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Table: salarios_base ---
    op.create_table(
        "salarios_base",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "rol", "desde", name="uq_salario_base_tenant_rol_desde"),
    )
    op.create_index(op.f("ix_salarios_base_tenant_id"), "salarios_base", ["tenant_id"], unique=False)

    # --- Table: salarios_plus ---
    op.create_table(
        "salarios_plus",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("grupo", sa.String(50), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "grupo", "rol", "desde", name="uq_salario_plus_tenant_grupo_rol_desde"),
    )
    op.create_index(op.f("ix_salarios_plus_tenant_id"), "salarios_plus", ["tenant_id"], unique=False)

    # --- Table: liquidaciones ---
    op.create_table(
        "liquidaciones",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("cohorte_id", sa.UUID(), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False),
        sa.Column("comisiones", postgresql.JSONB(), nullable=True),
        sa.Column("monto_base", sa.Numeric(10, 2), nullable=False),
        sa.Column("monto_plus", sa.Numeric(10, 2), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("es_nexo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("excluido_por_factura", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Abierta"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"], ),
        sa.ForeignKeyConstraint(["usuario_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "cohorte_id", "periodo", "usuario_id", name="uq_liquidacion_tenant_cohorte_periodo_usuario"),
    )
    op.create_index(op.f("ix_liquidaciones_tenant_id"), "liquidaciones", ["tenant_id"], unique=False)

    # --- Table: facturas ---
    op.create_table(
        "facturas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=False),
        sa.Column("referencia_archivo", sa.String(512), nullable=True),
        sa.Column("tamano_kb", sa.Numeric(10, 2), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Pendiente"),
        sa.Column("cargada_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("abonada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("materia_id", sa.UUID(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_facturas_tenant_id"), "facturas", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_facturas_usuario_id"), "facturas", ["usuario_id"], unique=False)
    op.create_index(op.f("ix_facturas_periodo"), "facturas", ["periodo"], unique=False)

    # --- ALTER TABLE materias ADD COLUMN grupo_plus ---
    op.add_column("materias", sa.Column("grupo_plus", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("materias", "grupo_plus")
    op.drop_table("facturas")
    op.drop_table("liquidaciones")
    op.drop_table("salarios_plus")
    op.drop_table("salarios_base")

