# identity-management Specification

## Purpose
TBD - created by archiving change core-models-y-tenancy. Update Purpose after archive.
## Requirements
### Requirement: User model with encrypted PII fields
The system SHALL provide a `User` model with the following attributes:
- `id`: UUID, PK, database-generated
- `tenant_id`: UUID, NOT NULL, FK to tenant
- `email`: EncryptedString, NOT NULL, unique per tenant
- `password_hash`: text, NOT NULL (Argon2id hash, never plaintext)
- `nombre`: text, NOT NULL
- `apellido`: text, NOT NULL
- `dni`: EncryptedString, nullable, unique per tenant when present
- `cuil`: EncryptedString, nullable, unique per tenant when present
- `cbu`: EncryptedString, nullable
- `alias_cbu`: EncryptedString, nullable
- `legajo`: text, nullable, unique per tenant (business attribute, NOT a credential)
- `telefono`: text, nullable
- `fecha_nacimiento`: date, nullable
- `created_at`, `updated_at`, `deleted_at`: from TenantMixin
- Relationships: `roles` (via UserRole), `tenants` (via UserTenant)

#### Scenario: User creation stores encrypted PII
- **WHEN** User is created with email, dni, cuil, cbu
- **THEN** database stores encrypted values; plaintext never written to DB

#### Scenario: User email uniqueness enforced per tenant
- **WHEN** attempting to create second User with same email in same tenant
- **THEN** unique constraint violation (on encrypted value)

#### Scenario: User legajo is unique per tenant but not a credential
- **WHEN** two users in different tenants have same legajo
- **THEN** both are allowed (uniqueness scoped to tenant)

#### Scenario: Password never stored in plaintext
- **WHEN** User.password_hash is inspected in database
- **THEN** value is Argon2id hash (starts with $argon2id$), never plaintext

### Requirement: Role model for RBAC
The system SHALL provide a `Role` model:
- `id`: UUID, PK
- `tenant_id`: UUID, NOT NULL, FK to tenant
- `nombre`: text, NOT NULL (e.g., 'PROFESOR', 'COORDINADOR', 'ALUMNO')
- `descripcion`: text, nullable
- `created_at`, `updated_at`, `deleted_at`: from TenantMixin
- Unique constraint: `(tenant_id, nombre)`
- Relationships: `permisos` (via RolePermiso), `usuarios` (via UserRole)

#### Scenario: Role names unique per tenant
- **WHEN** creating Role 'PROFESOR' in tenant A and tenant B
- **THEN** both succeed (scoped uniqueness)

### Requirement: Permission model with modulo:accion format
The system SHALL provide a `Permission` model:
- `id`: UUID, PK
- `nombre`: text, NOT NULL, UNIQUE globally (format `modulo:accion`, e.g., 'calificaciones:importar')
- `descripcion`: text, NOT NULL
- `modulo`: text, NOT NULL (derived from nombre before ':')
- `accion`: text, NOT NULL (derived from nombre after ':')
- Global uniqueness (not tenant-scoped — permissions are catalog)

#### Scenario: Permission nombre follows modulo:accion format
- **WHEN** creating Permission with nombre 'materias:crear'
- **THEN** modulo='materias', accion='crear' are extracted and stored

#### Scenario: Permission catalog is global (not tenant-scoped)
- **WHEN** listing permissions
- **THEN** same permissions available to all tenants

### Requirement: UserRole association with tenant scope
The system SHALL provide a `UserRole` model linking User → Role → tenant context:
- `id`: UUID, PK
- `user_id`: UUID, NOT NULL, FK to user
- `role_id`: UUID, NOT NULL, FK to role
- `tenant_id`: UUID, NOT NULL, FK to tenant
- `desde`: date, NOT NULL (vigencia inicio)
- `hasta`: date, nullable (vigencia fin; NULL = indefinido)
- `activo`: boolean, NOT NULL, default true
- Unique constraint: `(tenant_id, user_id, role_id)`
- NO soft delete (vigencia handles lifecycle)

#### Scenario: UserRole grants permission only within tenant and date range
- **WHEN** checking if user has role on date X
- **THEN** true only if `desde <= X <= hasta` (or hasta IS NULL) AND activo=true

### Requirement: UserTenant association for multi-tenant users
The system SHALL provide a `UserTenant` model:
- `id`: UUID, PK
- `user_id`: UUID, NOT NULL, FK to user
- `tenant_id`: UUID, NOT NULL, FK to tenant
- `activo`: boolean, NOT NULL, default true
- Unique constraint: `(user_id, tenant_id)`
- NO soft delete

#### Scenario: User can belong to multiple tenants
- **WHEN** UserTenant links user to tenant A and tenant B
- **THEN** user can authenticate in both tenants (separate sessions)

