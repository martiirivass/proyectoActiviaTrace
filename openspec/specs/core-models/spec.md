# core-models Specification

## Purpose
TBD - created by archiving change core-models-y-tenancy. Update Purpose after archive.
## Requirements
### Requirement: UUID primary keys for all domain entities
The system SHALL use UUID (v4, database-generated via `gen_random_uuid()`) as primary key for all domain tables:
- Column type: `UUID` (PostgreSQL native)
- Default: `gen_random_uuid()`
- No application-side UUID generation required

#### Scenario: New entity gets UUID on insert
- **WHEN** inserting a new domain entity without providing id
- **THEN** database generates UUID automatically; entity.id is populated on flush

#### Scenario: UUID uniqueness enforced by database
- **WHEN** attempting to insert duplicate UUID (extremely unlikely)
- **THEN** primary key constraint violation

### Requirement: Automatic timestamp management (created_at, updated_at)
The system SHALL automatically manage timestamps on all domain entities:
- `created_at`: TIMESTAMP WITH TIME ZONE, NOT NULL, set on INSERT only
- `updated_at`: TIMESTAMP WITH TIME ZONE, NOT NULL, set on INSERT and UPDATE
- Values set by database (server_default / onupdate) or SQLAlchemy events — NOT application code

#### Scenario: created_at set once on insert
- **WHEN** entity is inserted
- **THEN** created_at = current timestamp; subsequent updates do not change it

#### Scenario: updated_at refreshed on every update
- **WHEN** entity is updated
- **THEN** updated_at = current timestamp

### Requirement: Soft delete via deleted_at timestamp
The system SHALL implement soft delete using `deleted_at` TIMESTAMP WITH TIME ZONE:
- `deleted_at`: NULLABLE, default NULL
- Soft delete = set `deleted_at = now()`
- Hard delete = DELETE FROM table (restricted to migrations/seeding)
- Queries default to `WHERE deleted_at IS NULL`

#### Scenario: Soft delete hides entity from normal queries
- **WHEN** entity.soft_delete() is called
- **THEN** deleted_at is set; entity excluded from `repository.list()` and `repository.get()`

#### Scenario: Deleted entities accessible via explicit opt-in
- **WHEN** `repository.list_with_deleted()` is called
- **THEN** includes entities with deleted_at NOT NULL

#### Scenario: deleted_at timestamp records when deletion occurred
- **WHEN** soft delete is performed
- **THEN** deleted_at = timestamp of deletion (audit trail)

### Requirement: TenantMixin composable for all domain models
The system SHALL provide a `TenantMixin` that composes all base columns:
- `id` (UUID PK), `tenant_id` (FK), `created_at`, `updated_at`, `deleted_at`
- Applied via SQLAlchemy DeclarativeMixin pattern
- All domain models include this mixin (except link tables UserRole, UserTenant)

#### Scenario: Domain model with TenantMixin has all base columns
- **WHEN** defining class `Materia(TenantMixin, Base)`
- **THEN** resulting table has id, tenant_id, created_at, updated_at, deleted_at

### Requirement: Granular mixins for special cases
The system SHALL provide separate mixins for models needing subsets:
- `UUIDMixin`: only `id` (PK)
- `TimestampMixin`: only `created_at`, `updated_at`
- `SoftDeleteMixin`: only `deleted_at`
- Used by link tables (UserRole, UserTenant) which don't need full TenantMixin

#### Scenario: UserRole has UUID + tenant_id + vigencia but no soft delete
- **WHEN** inspecting UserRole table
- **THEN** has id, user_id, role_id, tenant_id, desde, hasta, activo; NO deleted_at

