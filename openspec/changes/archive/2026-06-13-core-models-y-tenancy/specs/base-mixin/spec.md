## ADDED Requirements

### Requirement: TenantMixin provides id, tenant_id, timestamps, and soft delete to domain models
The system SHALL provide a `TenantMixin` composable via SQLAlchemy DeclarativeMixin that adds the following columns to any model that includes it:
- `id`: UUID, primary key, database-generated
- `tenant_id`: UUID, NOT NULL, foreign key to `tenant.id`, composite index with other columns
- `created_at`: timestamp with timezone, NOT NULL, auto-set on insert
- `updated_at`: timestamp with timezone, NOT NULL, auto-set on insert and update
- `deleted_at`: timestamp with timezone, NULLABLE, set on soft delete

#### Scenario: Model including TenantMixin has all base columns
- **WHEN** a domain model class includes TenantMixin
- **THEN** the resulting table has columns id, tenant_id, created_at, updated_at, deleted_at

#### Scenario: tenant_id is NOT NULL and references tenant table
- **WHEN** inserting a row for a model with TenantMixin
- **THEN** tenant_id must be provided and must reference an existing tenant

#### Scenario: created_at auto-populated on insert
- **WHEN** a new row is inserted
- **THEN** created_at is set to current timestamp without application code setting it

#### Scenario: updated_at auto-populated on insert and update
- **WHEN** a row is inserted or updated
- **THEN** updated_at is set to current timestamp

#### Scenario: deleted_at is NULL by default
- **WHEN** a new row is inserted
- **THEN** deleted_at is NULL

### Requirement: TimestampMixin and SoftDeleteMixin as granular alternatives
The system SHALL provide separate `TimestampMixin` (created_at, updated_at) and `SoftDeleteMixin` (deleted_at) for models that need only subsets of the base functionality.

#### Scenario: Model with only TimestampMixin has created_at and updated_at
- **WHEN** a model includes only TimestampMixin
- **THEN** the table has created_at and updated_at but not tenant_id or deleted_at

#### Scenario: Model with only SoftDeleteMixin has deleted_at
- **WHEN** a model includes only SoftDeleteMixin
- **THEN** the table has deleted_at but not created_at or updated_at