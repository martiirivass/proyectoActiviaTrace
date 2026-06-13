# multi-tenancy Specification

## Purpose
TBD - created by archiving change core-models-y-tenancy. Update Purpose after archive.
## Requirements
### Requirement: Row-level multi-tenancy isolation for all domain entities
The system SHALL enforce tenant isolation at the database row level for every domain entity:
- Every domain table MUST have a `tenant_id` UUID column with NOT NULL constraint and FK to `tenant.id`
- Every query MUST filter by the authenticated session's `tenant_id` (from JWT)
- Cross-tenant data access MUST be impossible via normal query paths

#### Scenario: Tenant A cannot read Tenant B's data
- **WHEN** a query is executed with `tenant_id = tenant_a_id`
- **THEN** only rows where `tenant_id = tenant_a_id` are returned; Tenant B's rows are never visible

#### Scenario: Tenant A cannot write to Tenant B's data
- **WHEN** an INSERT/UPDATE is attempted with explicit `tenant_id = tenant_b_id` in a Tenant A session
- **THEN** the operation is rejected (repository raises ValueError on tenant_id mismatch)

#### Scenario: Tenant filter applied automatically by repository
- **WHEN** `repository.list()` is called
- **THEN** the generated SQL includes `WHERE tenant_id = :tenant_id AND deleted_at IS NULL`

#### Scenario: Soft delete filter applied automatically
- **WHEN** `repository.get(id)` is called for an entity with `deleted_at` set
- **THEN** returns None (entity hidden from normal queries)

#### Scenario: Explicit opt-in to include deleted entities
- **WHEN** `repository.list_with_deleted()` is called
- **THEN** returns all entities in tenant scope including soft-deleted ones

### Requirement: Tenant context derived exclusively from authenticated session
The system SHALL derive `tenant_id` ONLY from the verified JWT token in the request:
- `tenant_id` is a claim in the access token (set at login)
- No endpoint accepts `tenant_id` as parameter, header, or body
- Middleware/dependency extracts and validates tenant from token

#### Scenario: Request without valid JWT has no tenant context
- **WHEN** request lacks Authorization header or token is invalid/expired
- **THEN** authentication fails (401) before any tenant context is established

#### Scenario: Request with valid JWT gets tenant_id from token claims
- **WHEN** request includes valid access token with `tenant_id` claim
- **THEN** `tenant_id` is available to repositories via dependency injection

