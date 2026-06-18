## ADDED Requirements

### Requirement: System SHALL store roles as administrable catalog
The system SHALL provide a `Role` model with fields: `id` (UUID PK), `name` (unique per tenant, e.g. "PROFESOR"), `description` (text), `is_system` (boolean, system roles cannot be deleted), `tenant_id` (FK to tenant, nullable for system-wide roles), and audit fields (`created_at`, `updated_at`). Roles SHALL be stored as data in the database, not hardcoded in application code.

#### Scenario: Create a new role
- **WHEN** an admin creates a new role with name and description
- **THEN** the role is persisted in the `roles` table with a UUID and timestamps

#### Scenario: System role cannot be deleted
- **WHEN** attempting to delete a role with `is_system = true`
- **THEN** the system returns HTTP 400 with error detail "System roles cannot be deleted"

---

### Requirement: System SHALL store permissions as administrable catalog
The system SHALL provide a `Permission` model with fields: `id` (UUID PK), `codename` (unique, format `modulo:accion`, e.g. "calificaciones:importar"), `description` (text), `module` (text, e.g. "calificaciones"), `action` (text, e.g. "importar"). Permissions SHALL be created during seed migration and are not user-creatable (the catalog is extended via code/migration).

#### Scenario: Permission has correct format
- **WHEN** a permission is created with codename "atrasados:ver"
- **THEN** it is stored with module="atrasados" and action="ver"

---

### Requirement: System SHALL map roles to permissions via RolPermiso
The system SHALL provide a `RolePermission` association model with fields: `id` (UUID PK), `role_id` (FK to Role), `permission_id` (FK to Permission), `scope` (enum: "global" or "propio"), `tenant_id` (FK to Tenant). The `scope` field defines whether the permission applies globally or only to the user's own data. Unique constraint on `(role_id, permission_id)`.

#### Scenario: Assign permission to role
- **WHEN** a permission "calificaciones:importar" is assigned to role "PROFESOR" with scope "propio"
- **THEN** a RolPermiso record is created linking the role and permission with scope="propio"

---

### Requirement: System SHALL seed 7 domain roles with permission matrix
On initial migration, the system SHALL seed the following roles: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS. Each role SHALL be pre-configured with permissions matching the matrix defined in `03_actores_y_roles.md` §3.3. The seed SHALL include approximately 20 permissions covering all capabilities.

#### Scenario: ADMIN has all management permissions
- **WHEN** querying permissions for the ADMIN role
- **THEN** it includes "estructura:gestionar", "usuarios:gestionar", "equipos:asignar", "avisos:publicar", "auditoria:ver", "tenant:configurar"

#### Scenario: ALUMNO has only student permissions
- **WHEN** querying permissions for the ALUMNO role
- **THEN** it includes "estado:ver", "evaluacion:reservar", "avisos:confirmar" and no management permissions

#### Scenario: FINANZAS has only financial permissions
- **WHEN** querying permissions for the FINANZAS role
- **THEN** it includes "auditoria:ver", "liquidaciones:gestionar", "liquidaciones:calcular", "facturas:gestionar" and no academic management permissions

---

### Requirement: System SHALL resolve effective permissions per user
The system SHALL provide a function `PermissionService.get_effective_permissions(user_id)` that returns the set of all permissions for a user by: (1) finding all active roles for the user via UserRole, (2) joining with RolPermiso for each role, (3) returning a set of `"modulo:accion"` strings. Only non-expired UserRole assignments SHALL be considered.

#### Scenario: User with single role
- **WHEN** a user with only the PROFESOR role has their permissions resolved
- **THEN** the result includes "calificaciones:importar", "atrasados:ver", "comunicacion:enviar", "encuentros:gestionar", "tareas:gestionar", "avisos:confirmar"

#### Scenario: User with multiple roles (union)
- **WHEN** a user with both PROFESOR and COORDINADOR roles has their permissions resolved
- **THEN** the result includes the union of both role's permissions (e.g., both "calificaciones:importar" and "equipos:asignar")

#### Scenario: Expired role assignment excluded
- **WHEN** a user has a COORDINADOR assignment whose `hasta` date is in the past
- **THEN** the COORDINADOR permissions are NOT included in the effective set

---

### Requirement: System SHALL provide require_permission dependency
The system SHALL provide a FastAPI dependency `require_permission(codename: str)` that: (1) resolves the current user via `get_current_user`, (2) resolves effective permissions via `PermissionService`, (3) returns the user if the permission is found, (4) raises HTTP 403 if the permission is missing.

#### Scenario: User has required permission
- **WHEN** a user with "calificaciones:importar" accesses an endpoint with `require_permission("calificaciones:importar")`
- **THEN** the dependency passes and the request proceeds

#### Scenario: User lacks required permission
- **WHEN** a user without "liquidaciones:calcular" accesses an endpoint with `require_permission("liquidaciones:calcular")`
- **THEN** the dependency raises HTTP 403 with error detail "Forbidden: missing permission 'liquidaciones:calcular'"

#### Scenario: Unauthenticated user
- **WHEN** a request without a valid JWT accesses an endpoint with `require_permission(...)`
- **THEN** `get_current_user` raises HTTP 401 before the permission check
