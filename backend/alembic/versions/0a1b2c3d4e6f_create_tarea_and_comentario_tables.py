"""create tarea and comentario_tarea tables

Revision ID: 0a1b2c3d4e6f
Revises: f7a8b9c0d1e2
Create Date: 2026-06-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0a1b2c3d4e6f"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Create enum type ---
    op.execute("CREATE TYPE estado_tarea AS ENUM ('Pendiente', 'EnProgreso', 'Resuelta', 'Cancelada')")

    # --- Table: tareas ---
    op.create_table(
        "tareas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("materia_id", sa.UUID(), nullable=True),
        sa.Column("asignado_a", sa.UUID(), nullable=False),
        sa.Column("asignado_por", sa.UUID(), nullable=False),
        sa.Column(
            "estado",
            postgresql.ENUM("Pendiente", "EnProgreso", "Resuelta", "Cancelada", name="estado_tarea", create_type=False),
            nullable=False,
            server_default=sa.text("'Pendiente'"),
        ),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("contexto_id", sa.UUID(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.ForeignKeyConstraint(["asignado_a"], ["users.id"], ),
        sa.ForeignKeyConstraint(["asignado_por"], ["users.id"], ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tareas_tenant_id"), "tareas", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_tareas_materia_id"), "tareas", ["materia_id"], unique=False)
    op.create_index(op.f("ix_tareas_asignado_a"), "tareas", ["asignado_a"], unique=False)
    op.create_index(op.f("ix_tareas_asignado_por"), "tareas", ["asignado_por"], unique=False)
    op.create_index(op.f("ix_tareas_estado"), "tareas", ["estado"], unique=False)

    # --- Table: comentarios_tarea ---
    op.create_table(
        "comentarios_tarea",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("tarea_id", sa.UUID(), nullable=False),
        sa.Column("autor_id", sa.UUID(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("creado_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tarea_id"], ["tareas.id"], ),
        sa.ForeignKeyConstraint(["autor_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comentarios_tarea_tenant_id"), "comentarios_tarea", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_comentarios_tarea_tarea_id"), "comentarios_tarea", ["tarea_id"], unique=False)
    op.create_index(op.f("ix_comentarios_tarea_autor_id"), "comentarios_tarea", ["autor_id"], unique=False)


def downgrade() -> None:
    op.drop_table("comentarios_tarea")
    op.drop_table("tareas")
    op.execute("DROP TYPE IF EXISTS estado_tarea")
