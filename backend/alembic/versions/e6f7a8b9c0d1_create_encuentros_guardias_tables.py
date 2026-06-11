"""create encuentros and guardias tables

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-06-11 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Create enum types ---
    op.execute("CREATE TYPE dia_semana AS ENUM ('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo')")
    op.execute("CREATE TYPE estado_instancia AS ENUM ('Programado', 'Realizado', 'Cancelado')")
    op.execute("CREATE TYPE dia_guardia AS ENUM ('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo')")
    op.execute("CREATE TYPE estado_guardia AS ENUM ('Pendiente', 'Realizada', 'Cancelada')")

    # --- Table: slot_encuentro ---
    op.create_table(
        "slot_encuentro",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("asignacion_id", sa.UUID(), nullable=False),
        sa.Column("materia_id", sa.UUID(), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column(
            "dia_semana",
            postgresql.ENUM("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo", name="dia_semana", create_type=False),
            nullable=True,
        ),
        sa.Column("fecha_inicio", sa.Date(), nullable=True),
        sa.Column("cant_semanas", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("fecha_unica", sa.Date(), nullable=True),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignaciones.id"], ),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_slot_encuentro_tenant_id"), "slot_encuentro", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_slot_encuentro_asignacion_id"), "slot_encuentro", ["asignacion_id"], unique=False)
    op.create_index(op.f("ix_slot_encuentro_materia_id"), "slot_encuentro", ["materia_id"], unique=False)

    # --- Table: instancia_encuentro ---
    op.create_table(
        "instancia_encuentro",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("slot_id", sa.UUID(), nullable=True),
        sa.Column("materia_id", sa.UUID(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column(
            "estado",
            postgresql.ENUM("Programado", "Realizado", "Cancelado", name="estado_instancia", create_type=False),
            nullable=False,
            server_default="Programado",
        ),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("comentario", sa.String(1000), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["slot_id"], ["slot_encuentro.id"], ),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_instancia_encuentro_tenant_id"), "instancia_encuentro", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_instancia_encuentro_slot_id"), "instancia_encuentro", ["slot_id"], unique=False)
    op.create_index(op.f("ix_instancia_encuentro_materia_id"), "instancia_encuentro", ["materia_id"], unique=False)

    # --- Table: guardias ---
    op.create_table(
        "guardias",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("asignacion_id", sa.UUID(), nullable=False),
        sa.Column("materia_id", sa.UUID(), nullable=False),
        sa.Column("carrera_id", sa.UUID(), nullable=False),
        sa.Column("cohorte_id", sa.UUID(), nullable=False),
        sa.Column(
            "dia",
            postgresql.ENUM("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo", name="dia_guardia", create_type=False),
            nullable=False,
        ),
        sa.Column("horario", sa.String(50), nullable=False),
        sa.Column(
            "estado",
            postgresql.ENUM("Pendiente", "Realizada", "Cancelada", name="estado_guardia", create_type=False),
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column("comentarios", sa.String(500), nullable=True),
        sa.Column("creada_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignaciones.id"], ),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"], ),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_guardias_tenant_id"), "guardias", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_guardias_asignacion_id"), "guardias", ["asignacion_id"], unique=False)
    op.create_index(op.f("ix_guardias_materia_id"), "guardias", ["materia_id"], unique=False)
    op.create_index(op.f("ix_guardias_carrera_id"), "guardias", ["carrera_id"], unique=False)
    op.create_index(op.f("ix_guardias_cohorte_id"), "guardias", ["cohorte_id"], unique=False)


def downgrade() -> None:
    op.drop_table("guardias")
    op.drop_table("instancia_encuentro")
    op.drop_table("slot_encuentro")
    op.execute("DROP TYPE IF EXISTS estado_guardia")
    op.execute("DROP TYPE IF EXISTS dia_guardia")
    op.execute("DROP TYPE IF EXISTS estado_instancia")
    op.execute("DROP TYPE IF EXISTS dia_semana")
