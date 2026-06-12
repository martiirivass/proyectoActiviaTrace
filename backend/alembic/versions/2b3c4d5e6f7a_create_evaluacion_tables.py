"""create evaluacion tables (evaluaciones, dias_convocatoria, evaluacion_alumnos_convocados, reservas_evaluacion, resultados_evaluacion)

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2026-06-12 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "2b3c4d5e6f7a"
down_revision: Union[str, Sequence[str], None] = "1a2b3c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Create enums ---
    sa.Enum("Parcial", "TP", "Coloquio", "Recuperatorio", name="tipo_evaluacion").create(op.get_bind())
    sa.Enum("Activa", "Cancelada", name="estado_reserva").create(op.get_bind())
    sa.Enum("Borrador", "Definitivo", name="estado_resultado").create(op.get_bind())

    # --- evaluaciones ---
    op.create_table(
        "evaluaciones",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False, index=True),
        sa.Column("materia_id", sa.UUID(), nullable=False, index=True),
        sa.Column("cohorte_id", sa.UUID(), nullable=False, index=True),
        sa.Column(
            "tipo",
            sa.Enum("Parcial", "TP", "Coloquio", "Recuperatorio", name="tipo_evaluacion"),
            nullable=False,
        ),
        sa.Column("instancia", sa.String(length=255), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- dias_convocatoria ---
    op.create_table(
        "dias_convocatoria",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False, index=True),
        sa.Column("evaluacion_id", sa.UUID(), nullable=False, index=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("cupo_maximo", sa.Integer(), nullable=False),
        sa.Column("cupos_ocupados", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluaciones.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- evaluacion_alumnos_convocados ---
    op.create_table(
        "evaluacion_alumnos_convocados",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False, index=True),
        sa.Column("evaluacion_id", sa.UUID(), nullable=False, index=True),
        sa.Column("alumno_id", sa.UUID(), nullable=False, index=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluaciones.id"], ),
        sa.ForeignKeyConstraint(["alumno_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- reservas_evaluacion ---
    op.create_table(
        "reservas_evaluacion",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False, index=True),
        sa.Column("evaluacion_id", sa.UUID(), nullable=False, index=True),
        sa.Column("dia_convocatoria_id", sa.UUID(), nullable=False, index=True),
        sa.Column("alumno_id", sa.UUID(), nullable=False, index=True),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("Activa", "Cancelada", name="estado_reserva"),
            nullable=False,
            server_default="Activa",
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluaciones.id"], ),
        sa.ForeignKeyConstraint(["dia_convocatoria_id"], ["dias_convocatoria.id"], ),
        sa.ForeignKeyConstraint(["alumno_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- resultados_evaluacion ---
    op.create_table(
        "resultados_evaluacion",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False, index=True),
        sa.Column("evaluacion_id", sa.UUID(), nullable=False, index=True),
        sa.Column("alumno_id", sa.UUID(), nullable=False, index=True),
        sa.Column("nota_final", sa.String(length=50), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("Borrador", "Definitivo", name="estado_resultado"),
            nullable=False,
            server_default="Borrador",
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluaciones.id"], ),
        sa.ForeignKeyConstraint(["alumno_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("resultados_evaluacion")
    op.drop_table("reservas_evaluacion")
    op.drop_table("evaluacion_alumnos_convocados")
    op.drop_table("dias_convocatoria")
    op.drop_table("evaluaciones")

    sa.Enum(name="tipo_evaluacion").drop(op.get_bind())
    sa.Enum(name="estado_reserva").drop(op.get_bind())
    sa.Enum(name="estado_resultado").drop(op.get_bind())
