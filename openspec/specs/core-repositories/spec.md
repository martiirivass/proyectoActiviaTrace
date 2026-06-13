# core-repositories Specification

## Purpose
TBD - created by archiving change core-models-y-tenancy. Update Purpose after archive.
## Requirements
### Requirement: Generic Repository base class with mandatory tenant scope
The system SHALL provide a generic `Repository[T]` where `T` is a SQLAlchemy model including `TenantMixin`:
- Constructor: `Repository(session: AsyncSession, tenant_id: UUID)` — `tenant_id` required at instantiation
- All query methods automatically apply:
  - `WHERE model.tenant_id == self.tenant_id`
  - `WHERE model.deleted_at IS NULL` (soft delete filter)
- Type-safe: `T` bound to models with TenantMixin

#### Scenario: Repository cannot be instantiated without tenant_id
- **WHEN** `Repository(session)` called without tenant_id
- **THEN** TypeError (missing required argument)

#### Scenario: All queries filtered by tenant_id
- **WHEN** `repository.list()` executed
- **THEN** SQL includes `WHERE tenant_id = :tenant_id`

#### Scenario: All queries filtered by deleted_at IS NULL by default
- **WHEN** `repository.get(id)` executed
- **THEN** SQL includes `WHERE deleted_at IS NULL`

### Requirement: Standard CRUD methods with tenant enforcement
The system SHALL provide the following methods on `Repository[T]`:

- `get(id: UUID) -> T | None`: Single entity by PK, tenant-scoped, excludes deleted
- `list() -> list[T]`: All entities in tenant, excludes deleted, ordered by created_at desc
- `list_with_deleted() -> list[T]`: All entities in tenant, includes deleted (audit/admin only)
- `count() -> int`: Count of non-deleted entities in tenant
- `exists(id: UUID) -> bool`: True if entity exists in tenant and not deleted
- `create(**kwargs) -> T`: Insert new entity; sets `tenant_id = self.tenant_id` automatically; rejects explicit `tenant_id` mismatch
- `update(instance: T, **kwargs) -> T`: Update entity; preserves `tenant_id` (raises if changed)
- `delete(instance: T) -> None`: Soft delete (sets `deleted_at = now()`)
- `hard_delete(instance: T) -> None`: Permanent delete; RESTRICTED to migrations/seeding only

#### Scenario: create() auto-sets tenant_id
- **WHEN** `repository.create(nombre="Test")`
- **THEN** inserted row has `tenant_id = repository.tenant_id`

#### Scenario: create() rejects explicit tenant_id mismatch
- **WHEN** `repository.create(tenant_id=other_id, nombre="Test")`
- **THEN** ValueError raised

#### Scenario: update() preserves tenant_id
- **WHEN** `repository.update(entity, tenant_id=other_id)`
- **THEN** ValueError raised (tenant_id immutable)

#### Scenario: delete() performs soft delete
- **WHEN** `repository.delete(entity)`
- **THEN** entity.deleted_at set; row remains in table

#### Scenario: hard_delete() removes row permanently
- **WHEN** `repository.hard_delete(entity)`
- **THEN** row deleted from database

#### Scenario: count() excludes deleted
- **WHEN** `repository.count()`
- **THEN** COUNT(*) WHERE tenant_id = ? AND deleted_at IS NULL

#### Scenario: exists() checks tenant scope
- **WHEN** `repository.exists(id_of_other_tenant)`
- **THEN** False

### Requirement: Derived repositories cannot bypass tenant filter
The system SHALL ensure any class inheriting from `Repository[T]` inherits tenant enforcement:
- Custom query methods in derived repos MUST include `.where(Model.tenant_id == self.tenant_id)`
- Code review rejects any `session.execute(select(Model))` without tenant filter
- Linter rule (future): flag raw queries without tenant_id

#### Scenario: Custom method in derived repo respects tenant scope
- **WHEN** `class MateriaRepository(Repository[Materia]): def activos(self): return self.session.execute(select(Materia).where(Materia.activa==True))`
- **THEN** code review rejects (missing `.where(Materia.tenant_id == self.tenant_id)`)

#### Scenario: Correct custom method includes tenant filter
- **WHEN** `def activos(self): return self.session.execute(select(Materia).where(Materia.tenant_id == self.tenant_id, Materia.activa==True))`
- **THEN** passes review

### Requirement: Repository factory for dependency injection
The system SHALL provide a factory function `get_repository(model_class, tenant_id)` for FastAPI dependency injection:
- Used in Services to obtain repository instances
- `tenant_id` sourced from authenticated request context (C-03)

#### Scenario: Service obtains repository via factory
- **WHEN** `materia_repo = get_repository(Materia, tenant_id)`
- **THEN** `materia_repo` is `Repository[Materia]` with tenant_id set

