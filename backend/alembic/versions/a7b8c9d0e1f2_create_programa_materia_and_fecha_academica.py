"""create programa_materia and fecha_academica tables

Revision ID: a7b8c9d0e1f2
Revises: 35d1ca4ee0c6
Create Date: 2026-06-12 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "35d1ca4ee0c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create programas_materia table
    op.create_table(
        "programas_materia",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("materia_id", UUID(as_uuid=True), sa.ForeignKey("materias.id"), nullable=False, index=True),
        sa.Column("carrera_id", UUID(as_uuid=True), sa.ForeignKey("carreras.id"), nullable=False, index=True),
        sa.Column("cohorte_id", UUID(as_uuid=True), sa.ForeignKey("cohortes.id"), nullable=False, index=True),
        sa.Column("titulo", sa.String(500), nullable=False),
        sa.Column("referencia_archivo", sa.String(500), nullable=True),
        sa.Column("cargado_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "materia_id", "carrera_id", "cohorte_id",
            name="uq_programa_materia_carrera_cohorte",
        ),
    )

    # Create fechas_academicas table
    op.create_table(
        "fechas_academicas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("materia_id", UUID(as_uuid=True), sa.ForeignKey("materias.id"), nullable=False, index=True),
        sa.Column("cohorte_id", UUID(as_uuid=True), sa.ForeignKey("cohortes.id"), nullable=False, index=True),
        sa.Column("tipo", sa.Enum("Parcial", "TP", "Coloquio", "Recuperatorio", name="tipofecha"), nullable=False, index=True),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False, index=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("titulo", sa.String(500), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "materia_id", "cohorte_id", "tipo", "numero", "periodo",
            name="uq_fecha_materia_cohorte_tipo_numero_periodo",
        ),
    )


def downgrade() -> None:
    op.drop_table("fechas_academicas")
    op.drop_table("programas_materia")
    op.execute("DROP TYPE IF EXISTS tipofecha")
