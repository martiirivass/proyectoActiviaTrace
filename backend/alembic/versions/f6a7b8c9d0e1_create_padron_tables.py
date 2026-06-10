"""create padron tables (version_padron, entrada_padron) and add moodle_integration_enabled to materias

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-10 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Seed permissions for padron-ingesta-moodle ---
    import uuid
    permissions_table = sa.table(
        "permissions",
        sa.Column("id", sa.UUID()),
        sa.Column("name", sa.String()),
        sa.Column("module", sa.String()),
        sa.Column("action", sa.String()),
        sa.Column("description", sa.String()),
    )
    padron_permissions = [
        {"name": "padron:cargar", "module": "padron", "action": "cargar", "description": "Cargar padrón de alumnos"},
        {"name": "padron:ver", "module": "padron", "action": "ver", "description": "Ver versiones de padrón"},
        {"name": "padron:vaciar", "module": "padron", "action": "vaciar", "description": "Vaciar datos de padrón de una materia"},
        {"name": "moodle:sync", "module": "moodle", "action": "sync", "description": "Sincronizar con Moodle Web Services"},
    ]
    for p in padron_permissions:
        op.execute(
            sa.insert(permissions_table).values(
                id=uuid.uuid4(),
                name=p["name"],
                module=p["module"],
                action=p["action"],
                description=p["description"],
            )
        )

    op.create_table(
        "version_padron",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("materia_id", sa.UUID(), nullable=False),
        sa.Column("cohorte_id", sa.UUID(), nullable=False),
        sa.Column("cargado_por", sa.UUID(), nullable=False),
        sa.Column("cargado_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], ),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"], ),
        sa.ForeignKeyConstraint(["cargado_por"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_version_padron_tenant_id"), "version_padron", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_version_padron_materia_id"), "version_padron", ["materia_id"], unique=False)
    op.create_index(op.f("ix_version_padron_cohorte_id"), "version_padron", ["cohorte_id"], unique=False)
    op.create_index(
        "uq_version_padron_activa",
        "version_padron",
        ["tenant_id", "materia_id", "cohorte_id"],
        unique=True,
        postgresql_where=sa.text("activa = true"),
    )

    op.create_table(
        "entrada_padron",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("version_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("apellidos", sa.String(255), nullable=False),
        sa.Column("email", sa.String(500), nullable=True),
        sa.Column("comision", sa.String(50), nullable=True),
        sa.Column("regional", sa.String(255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["version_padron.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_entrada_padron_version_id"), "entrada_padron", ["version_id"], unique=False)
    op.create_index(op.f("ix_entrada_padron_tenant_id"), "entrada_padron", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_entrada_padron_usuario_id"), "entrada_padron", ["usuario_id"], unique=False)

    op.add_column("materias", sa.Column("moodle_integration_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False))


def downgrade() -> None:
    op.drop_column("materias", "moodle_integration_enabled")
    op.drop_table("entrada_padron")
    op.drop_index("uq_version_padron_activa", table_name="version_padron", postgresql_where=sa.text("activa = true"))
    op.drop_table("version_padron")
