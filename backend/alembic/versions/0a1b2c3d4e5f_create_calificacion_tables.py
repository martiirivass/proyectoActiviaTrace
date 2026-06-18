"""create calificacion and umbral_materia tables

Revision ID: 0a1b2c3d4e5f
Revises: f6a7b8c9d0e1
Create Date: 2026-06-10 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0a1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Create enum type ---
    op.execute("CREATE TYPE origen_calificacion AS ENUM ('Importado', 'Manual')")

    # --- Table: calificacion ---
    op.create_table(
        "calificacion",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("entrada_padron_id", sa.UUID(), nullable=False),
        sa.Column("materia_id", sa.UUID(), nullable=False),
        sa.Column("actividad", sa.String(255), nullable=False),
        sa.Column("nota_numerica", sa.Float(), nullable=True),
        sa.Column("nota_textual", sa.String(255), nullable=True),
        sa.Column("aprobado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "origen",
            postgresql.ENUM("Importado", "Manual", name="origen_calificacion", create_type=False),
            nullable=False,
            server_default="Importado",
        ),
        sa.Column("importado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["entrada_padron_id"], ["entrada_padron.id"], ),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_calificacion_tenant_id"), "calificacion", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_calificacion_entrada_padron_id"), "calificacion", ["entrada_padron_id"], unique=False)
    op.create_index(op.f("ix_calificacion_materia_id"), "calificacion", ["materia_id"], unique=False)
    op.create_index(
        "ix_calificacion_tenant_materia_actividad",
        "calificacion",
        ["tenant_id", "materia_id", "actividad"],
        unique=False,
    )

    # --- Table: umbral_materia ---
    op.create_table(
        "umbral_materia",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("asignacion_id", sa.UUID(), nullable=False),
        sa.Column("materia_id", sa.UUID(), nullable=False),
        sa.Column("umbral_pct", sa.Integer(), nullable=False, server_default=sa.text("60")),
        sa.Column("valores_aprobatorios", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignaciones.id"], ),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "asignacion_id"),
    )
    op.create_index(op.f("ix_umbral_materia_tenant_id"), "umbral_materia", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_umbral_materia_asignacion_id"), "umbral_materia", ["asignacion_id"], unique=False)
    op.create_index(op.f("ix_umbral_materia_materia_id"), "umbral_materia", ["materia_id"], unique=False)


def downgrade() -> None:
    op.drop_table("umbral_materia")
    op.drop_table("calificacion")
    op.execute("DROP TYPE IF EXISTS origen_calificacion")
