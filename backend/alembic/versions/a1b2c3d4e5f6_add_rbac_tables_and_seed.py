"""add rbac tables (is_system, module/action, role_permissions) and seed data

Revision ID: a1b2c3d4e5f6
Revises: c3a7b8f9d0e1
Create Date: 2026-06-09 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c3a7b8f9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Add is_system to roles ---
    op.add_column('roles',
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )

    # --- Add module, action, updated_at to permissions ---
    op.add_column('permissions',
        sa.Column('module', sa.String(length=50), nullable=False, server_default='')
    )
    op.add_column('permissions',
        sa.Column('action', sa.String(length=50), nullable=False, server_default='')
    )
    op.add_column('permissions',
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False)
    )

    # --- Create role_permissions table ---
    op.create_table('role_permissions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.Column('permission_id', sa.UUID(), nullable=False),
        sa.Column('scope', sa.String(length=20), nullable=False, server_default='global'),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
    )

    # --- Seed data ---
    # First, get references to the tables for data operations
    permissions_table = sa.table('permissions',
        sa.Column('id', sa.UUID()),
        sa.Column('name', sa.String()),
        sa.Column('module', sa.String()),
        sa.Column('action', sa.String()),
        sa.Column('description', sa.String()),
        sa.Column('is_deleted', sa.Boolean()),
    )

    roles_table = sa.table('roles',
        sa.Column('id', sa.UUID()),
        sa.Column('name', sa.String()),
        sa.Column('description', sa.String()),
        sa.Column('is_system', sa.Boolean()),
        sa.Column('tenant_id', sa.UUID()),
        sa.Column('is_deleted', sa.Boolean()),
    )

    role_permissions_table = sa.table('role_permissions',
        sa.Column('id', sa.UUID()),
        sa.Column('role_id', sa.UUID()),
        sa.Column('permission_id', sa.UUID()),
        sa.Column('scope', sa.String()),
        sa.Column('tenant_id', sa.UUID()),
    )

    # We need a tenant for the seed data. Use the first tenant or create one.
    # Since this is domain seed data that should be available across tenants,
    # we use a well-known tenant UUID. For now, we'll reference existing tenants.
    # If no tenant exists, we create a system tenant.
    conn = op.get_bind()

    # --- Seed Permissions ---
    permission_data = [
        # modulo:accion
        {"name": "estado:ver", "module": "estado", "action": "ver",
         "description": "Ver estado de cursada"},
        {"name": "evaluacion:reservar", "module": "evaluacion", "action": "reservar",
         "description": "Reservar evaluación"},
        {"name": "avisos:confirmar", "module": "avisos", "action": "confirmar",
         "description": "Confirmar avisos"},
        {"name": "calificaciones:importar", "module": "calificaciones", "action": "importar",
         "description": "Importar calificaciones desde Moodle"},
        {"name": "atrasados:ver", "module": "atrasados", "action": "ver",
         "description": "Ver atrasados (scope propio)"},
        {"name": "entregas:detectar", "module": "entregas", "action": "detectar",
         "description": "Detectar entregas atrasadas"},
        {"name": "comunicacion:enviar", "module": "comunicacion", "action": "enviar",
         "description": "Enviar comunicación"},
        {"name": "comunicacion:aprobar", "module": "comunicacion", "action": "aprobar",
         "description": "Aprobar comunicación saliente"},
        {"name": "encuentros:gestionar", "module": "encuentros", "action": "gestionar",
         "description": "Gestionar encuentros"},
        {"name": "guardias:registrar", "module": "guardias", "action": "registrar",
         "description": "Registrar guardias"},
        {"name": "tareas:gestionar", "module": "tareas", "action": "gestionar",
         "description": "Gestionar tareas"},
        {"name": "avisos:publicar", "module": "avisos", "action": "publicar",
         "description": "Publicar avisos"},
        {"name": "equipos:asignar", "module": "equipos", "action": "asignar",
         "description": "Asignar equipos docentes"},
        {"name": "estructura:gestionar", "module": "estructura", "action": "gestionar",
         "description": "Gestionar estructura académica"},
        {"name": "usuarios:gestionar", "module": "usuarios", "action": "gestionar",
         "description": "Gestionar usuarios del sistema"},
        {"name": "auditoria:ver", "module": "auditoria", "action": "ver",
         "description": "Ver log de auditoría"},
        {"name": "liquidaciones:gestionar", "module": "liquidaciones", "action": "gestionar",
         "description": "Gestionar liquidaciones"},
        {"name": "liquidaciones:calcular", "module": "liquidaciones", "action": "calcular",
         "description": "Calcular liquidaciones"},
        {"name": "facturas:gestionar", "module": "facturas", "action": "gestionar",
         "description": "Gestionar facturas"},
        {"name": "tenant:configurar", "module": "tenant", "action": "configurar",
         "description": "Configurar tenant"},
        {"name": "impersonacion:usar", "module": "impersonacion", "action": "usar",
         "description": "Usar impersonación"},
    ]

    # Insert permissions and collect IDs by name
    import uuid as _uuid
    permission_ids = {}
    for p in permission_data:
        pid = _uuid.uuid4()
        permission_ids[p["name"]] = pid
        op.execute(
            sa.insert(permissions_table).values(
                id=pid,
                name=p["name"],
                module=p["module"],
                action=p["action"],
                description=p["description"],
                is_deleted=False,
            )
        )

    # --- Seed Roles ---
    role_defs = [
        {"name": "ALUMNO", "description": "Alumno del establecimiento"},
        {"name": "TUTOR", "description": "Tutor del alumno"},
        {"name": "PROFESOR", "description": "Profesor / docente"},
        {"name": "COORDINADOR", "description": "Coordinador académico"},
        {"name": "NEXO", "description": "Nexo institucional"},
        {"name": "ADMIN", "description": "Administrador del sistema"},
        {"name": "FINANZAS", "description": "Gestión financiera"},
    ]

    # Create or get a system tenant for seed data
    # Check if any tenant exists; if not, create a placeholder
    import uuid
    result = conn.execute(sa.text("SELECT id FROM tenants LIMIT 1"))
    row = result.fetchone()
    if row:
        default_tenant_id = row[0]
    else:
        default_tenant_id = uuid.uuid4()
        op.execute(
            sa.insert(sa.table('tenants',
                sa.Column('id', sa.UUID()),
                sa.Column('name', sa.String()),
                sa.Column('code', sa.String()),
                sa.Column('is_active', sa.Boolean()),
                sa.Column('is_deleted', sa.Boolean()),
            )).values(
                id=default_tenant_id,
                name="System",
                code="SYS",
                is_active=True,
                is_deleted=False,
            )
        )

    role_ids = {}
    for i, rd in enumerate(role_defs):
        rid = uuid.uuid4()
        role_ids[rd["name"]] = rid
        is_sys = rd["name"] in ("ADMIN", "FINANZAS")
        op.execute(
            sa.insert(roles_table).values(
                id=rid,
                name=rd["name"],
                description=rd["description"],
                is_system=is_sys,
                tenant_id=default_tenant_id,
                is_deleted=False,
            )
        )

    # --- Seed Role-Permission assignments ---
    # Matrix: which roles get which permissions, and with what scope
    # (scope "propio" means the permission only applies to own data)
    rp_matrix = {
        "ALUMNO": [
            ("estado:ver", "global"),
            ("evaluacion:reservar", "global"),
            ("avisos:confirmar", "global"),
        ],
        "TUTOR": [
            ("estado:ver", "propio"),
            ("avisos:confirmar", "global"),
            ("comunicacion:enviar", "global"),
        ],
        "PROFESOR": [
            ("estado:ver", "global"),
            ("calificaciones:importar", "global"),
            ("atrasados:ver", "propio"),
            ("entregas:detectar", "global"),
            ("comunicacion:enviar", "global"),
            ("encuentros:gestionar", "global"),
            ("guardias:registrar", "global"),
            ("tareas:gestionar", "global"),
            ("avisos:publicar", "global"),
        ],
        "COORDINADOR": [
            ("estado:ver", "global"),
            ("calificaciones:importar", "global"),
            ("atrasados:ver", "global"),
            ("entregas:detectar", "global"),
            ("comunicacion:enviar", "global"),
            ("comunicacion:aprobar", "global"),
            ("encuentros:gestionar", "global"),
            ("guardias:registrar", "global"),
            ("tareas:gestionar", "global"),
            ("avisos:publicar", "global"),
            ("equipos:asignar", "global"),
            ("estructura:gestionar", "global"),
        ],
        "NEXO": [
            ("estado:ver", "global"),
            ("comunicacion:enviar", "global"),
            ("encuentros:gestionar", "global"),
        ],
        "ADMIN": [
            ("estado:ver", "global"),
            ("calificaciones:importar", "global"),
            ("atrasados:ver", "global"),
            ("entregas:detectar", "global"),
            ("comunicacion:enviar", "global"),
            ("comunicacion:aprobar", "global"),
            ("encuentros:gestionar", "global"),
            ("guardias:registrar", "global"),
            ("tareas:gestionar", "global"),
            ("avisos:publicar", "global"),
            ("equipos:asignar", "global"),
            ("estructura:gestionar", "global"),
            ("usuarios:gestionar", "global"),
            ("auditoria:ver", "global"),
            ("tenant:configurar", "global"),
            ("impersonacion:usar", "global"),
        ],
        "FINANZAS": [
            ("liquidaciones:gestionar", "global"),
            ("liquidaciones:calcular", "global"),
            ("facturas:gestionar", "global"),
            ("auditoria:ver", "global"),
        ],
    }

    for role_name, perm_list in rp_matrix.items():
        rid = role_ids[role_name]
        for perm_name, scope in perm_list:
            pid = permission_ids[perm_name]
            rpid = uuid.uuid4()
            op.execute(
                sa.insert(role_permissions_table).values(
                    id=rpid,
                    role_id=rid,
                    permission_id=pid,
                    scope=scope,
                    tenant_id=default_tenant_id,
                )
            )


def downgrade() -> None:
    op.drop_table('role_permissions')
    op.drop_column('permissions', 'updated_at')
    op.drop_column('permissions', 'action')
    op.drop_column('permissions', 'module')
    op.drop_column('roles', 'is_system')
