## ADDED Requirements

### Requirement: Permission catalog with modulo:accion format
The system SHALL maintain a global catalog of permissions identified by `modulo:accion` strings:
- `Permission` table: `id` (UUID), `nombre` (text, UNIQUE, format `modulo:accion`), `descripcion` (text), `modulo` (text), `accion` (text)
- Examples: `calificaciones:importar`, `materias:crear`, `comunicacion:aprobar`, `equipos:asignar`, `auditoria:ver`
- Permissions are **global catalog** (not tenant-scoped) — same permissions available to all tenants
- `modulo` and `accion` extracted from `nombre` for grouping/filtering

#### Scenario: Permission nombre follows modulo:accion format
- **WHEN** creating Permission with nombre 'calificaciones:importar'
- **THEN** modulo='calificaciones', accion='importar' stored

#### Scenario: Permissions are globally unique
- **WHEN** listing permissions
- **THEN** each nombre appears once across all tenants

### Requirement: Role model with tenant-scoped names
The system SHALL provide tenant-scoped roles:
- `Role` table: `id` (UUID), `tenant_id` (FK), `nombre` (text), `descripcion` (text)
- Unique constraint: `(tenant_id, nombre)` — same role name can exist in different tenants
- Standard roles (seed in C-04): ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS

#### Scenario: Role 'PROFESOR' can exist in tenant A and tenant B
- **WHEN** creating Role 'PROFESOR' in both tenants
- **THEN** both succeed (different tenant_id)

### Requirement: Role-Permission matrix (data-driven, not hardcoded)
The system SHALL link roles to permissions via `RolePermiso` association table:
- `RolePermiso`: `role_id` (FK), `permiso_id` (FK), `tenant_id` (FK for partitioning), `created_at`
- Unique constraint: `(tenant_id, role_id, permiso_id)`
- **No hardcoded role-permission logic in code** — all resolved from this table at runtime
- Seeded in C-04 migration 002 per KB `03_actores_y_roles.md` §3.3

#### Scenario: Role effective permissions = union of its RolePermiso rows
- **WHEN** checking if Role X has Permission Y in tenant Z
- **THEN** true iff `RolePermiso` row exists for (role_id=X, permiso_id=Y, tenant_id=Z)

#### Scenario: Adding permission to role is data change, not code change
- **WHEN** admin inserts row into RolePermiso
- **THEN** role immediately gains that permission (no deploy needed)

### Requirement: User effective permissions via UserRole + RolePermiso
The system SHALL resolve user permissions by joining UserRole → RolePermiso → Permission:
- User's roles from `UserRole` where `user_id=X`, `tenant_id=Z`, `activo=true`, `desde <= today <= hasta` (or hasta IS NULL)
- For each role, collect permissions from `RolePermiso` where `role_id=role.id`, `tenant_id=Z`
- Union of all permissions = user's effective permissions in that tenant

#### Scenario: User with multiple roles gets union of permissions
- **WHEN** user has Role A (perms 1,2) and Role B (perms 2,3)
- **THEN** effective permissions = {1, 2, 3}

#### Scenario: Expired UserRole does not grant permissions
- **WHEN** UserRole.hasta < today
- **THEN** that role excluded from permission resolution

#### Scenario: Inactive UserRole does not grant permissions
- **WHEN** UserRole.activo = false
- **THEN** that role excluded from permission resolution

### Requirement: require_permission guard for endpoints
The system SHALL provide a FastAPI dependency `require_permission("modulo:accion")`:
- Declares required permission on each endpoint
- Resolves current user's effective permissions (from JWT + UserRole + RolePermiso)
- Returns 403 Forbidden if permission not granted
- **Fail-closed**: no explicit permission = 403

#### Scenario: Endpoint with require_permission('calificaciones:importar') grants access to user with permission
- **WHEN** user with 'calificaciones:importar' calls endpoint
- **THEN** 200 OK

#### Scenario: Endpoint with require_permission denies user without permission
- **WHEN** user without 'calificaciones:importar' calls endpoint
- **THEN** 403 Forbidden

#### Scenario: Endpoint without require_permission is not allowed (fail-closed)
- **WHEN** endpoint lacks require_permission dependency
- **THEN** code review rejects (all endpoints must declare permissions)