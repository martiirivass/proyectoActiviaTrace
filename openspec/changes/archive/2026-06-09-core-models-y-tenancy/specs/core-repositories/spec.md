## ADDED Requirements

### Requirement: Base repository with CRUD
The system SHALL provide a generic base repository with create, get, list, update, and soft-delete methods.

#### Scenario: Create entity
- **WHEN** creating an entity via repository
- **THEN** the entity SHALL be persisted in the database

#### Scenario: Get by id
- **WHEN** retrieving an entity by its UUID
- **THEN** the correct entity SHALL be returned, or None if not found

#### Scenario: List entities
- **WHEN** listing entities
- **THEN** all non-deleted entities SHALL be returned

#### Scenario: Update entity
- **WHEN** updating an entity's fields
- **THEN** the changes SHALL be persisted

#### Scenario: Soft delete entity
- **WHEN** deleting an entity via repository
- **THEN** the entity SHALL be soft-deleted (not hard-deleted)

### Requirement: Tenant-scoped repository
The system SHALL provide a `TenantScopedRepository` that automatically applies tenant_id filtering.

#### Scenario: Tenant-scoped get
- **WHEN** getting an entity with tenant_id
- **THEN** only entities matching that tenant SHALL be returned

#### Scenario: Tenant-scoped list
- **WHEN** listing entities with tenant_id
- **THEN** only entities belonging to that tenant SHALL be returned

#### Scenario: Tenant-scoped create
- **WHEN** creating an entity with tenant_id
- **THEN** the entity SHALL be created with that tenant_id
