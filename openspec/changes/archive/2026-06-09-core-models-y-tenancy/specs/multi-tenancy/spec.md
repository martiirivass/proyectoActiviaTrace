## ADDED Requirements

### Requirement: Tenant isolation via tenant_id
Every domain table SHALL include a `tenant_id` column referencing the Tenant table. All queries SHALL filter by tenant_id by default.

#### Scenario: Entity creation with tenant
- **WHEN** an entity is created with tenant_id
- **THEN** the entity SHALL be scoped to that tenant

#### Scenario: Cross-tenant isolation
- **WHEN** querying entities for tenant A
- **THEN** entities belonging to tenant B SHALL NOT be returned

### Requirement: Tenant context resolver
The system SHALL provide a mechanism to resolve the current tenant from the request context.

#### Scenario: Resolve tenant from context
- **WHEN** a request has a valid tenant context
- **THEN** the tenant_id SHALL be available for repository filtering

### Requirement: Fail-closed tenancy
The system SHALL prevent any query from executing without an explicit tenant scope.

#### Scenario: Query without tenant scope
- **WHEN** a repository query is attempted without tenant_id
- **THEN** the query SHALL raise an error or default to empty results
