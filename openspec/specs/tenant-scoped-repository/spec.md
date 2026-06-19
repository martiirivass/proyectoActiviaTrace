# tenant-scoped-repository Specification

## Purpose
TBD - created by archiving change core-models-y-tenancy. Update Purpose after archive.
## Requirements
### Requirement: Repository base class enforces tenant scope on all queries
The system SHALL provide a generic `Repository[T]` base class where `T` is a model type including `TenantMixin`. The repository:
- Requires `tenant_id: UUID` at construction time (injected from authenticated session)
- All query methods automatically filter by `model.tenant_id == self.tenant_id`
- All query methods automatically filter by `model.deleted_at IS NULL` (soft delete)
- Exposes `get(id)`, `list()`, `list_with_deleted()`, `count()`, `exists(id)`, `create(**kwargs)`, `update(instance, **kwargs)`, `delete(instance)`, `hard_delete(instance)` (restricted)

#### Scenario: Repository construction requires tenant_id
- **WHEN** instantiating Repository without tenant_id
- **THEN** TypeError is raised (missing required argument)

#### Scenario: get() returns entity only if tenant matches and not deleted
- **WHEN** calling repository.get(id) for an entity belonging to a different tenant
- **THEN** returns None (entity not found in this tenant's scope)

#### Scenario: get() returns entity if tenant matches and not deleted
- **WHEN** calling repository.get(id) for an entity in the same tenant with deleted_at NULL
- **THEN** returns the entity

#### Scenario: list() returns only non-deleted entities in tenant scope
- **WHEN** calling repository.list()
- **THEN** returns only entities where tenant_id matches AND deleted_at IS NULL

#### Scenario: list_with_deleted() returns all entities in tenant scope including deleted
- **WHEN** calling repository.list_with_deleted()
- **THEN** returns all entities where tenant_id matches (including deleted_at NOT NULL)

#### Scenario: create() sets tenant_id automatically
- **WHEN** calling repository.create(**kwargs) without tenant_id in kwargs
- **THEN** the created entity has tenant_id = repository.tenant_id

#### Scenario: create() rejects explicit tenant_id mismatch
- **WHEN** calling repository.create(tenant_id=other_tenant_id, ...)
- **THEN** raises ValueError (tenant_id mismatch)

#### Scenario: update() preserves tenant_id
- **WHEN** calling repository.update(instance, tenant_id=other_tenant_id)
- **THEN** raises ValueError (tenant_id cannot be changed)

#### Scenario: delete() performs soft delete
- **WHEN** calling repository.delete(instance)
- **THEN** instance.deleted_at is set to current timestamp, instance is flushed, no row removed

#### Scenario: hard_delete() removes row permanently (restricted)
- **WHEN** calling repository.hard_delete(instance)
- **THEN** row is deleted from database; only allowed in migrations/seeding contexts

#### Scenario: count() returns count of non-deleted entities in tenant
- **WHEN** calling repository.count()
- **THEN** returns COUNT(*) WHERE tenant_id = self.tenant_id AND deleted_at IS NULL

#### Scenario: exists() checks existence in tenant scope
- **WHEN** calling repository.exists(id) for entity in different tenant
- **THEN** returns False

### Requirement: Derived repositories inherit tenant enforcement
The system SHALL ensure that any class inheriting from `Repository[T]` cannot bypass the tenant filter.

#### Scenario: Custom query method in derived repository respects tenant scope
- **WHEN** a derived repository adds a custom method using `self.session.execute(select(Model))`
- **THEN** the query must include `.where(Model.tenant_id == self.tenant_id)` or it fails code review

