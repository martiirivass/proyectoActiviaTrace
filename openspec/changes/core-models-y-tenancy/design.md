## Context

This design implements the foundational domain models and multi-tenancy infrastructure for activia-trace (C-02). It builds on C-01's foundation (FastAPI skeleton, async SQLAlchemy, Alembic, Docker, observability) to create the core entities that all subsequent domain functionality depends on.

**Current state**: C-01 complete — backend structure, config, database connection, health checks, OpenTelemetry, reserved core slots (security, permissions, tenancy, exceptions).

**Stakeholders**: Backend team, security reviewers, future domain implementers (C-03 through C-24).

**Constraints**:
- Multi-tenancy row-level isolation (tenant_id on every table, default filtering)
- RBAC fino `modulo:accion` with fail-closed enforcement
- Clean Architecture: Models → Repositories → Services → Routers
- Strict TDD: test first, then implementation
- No DB mocks — real PostgreSQL test container
- AES-256 for PII (DNI, CBU), Argon2id for passwords
- Soft delete always (audit append-only)
- UUID internal identity, legajo as business attribute

## Goals / Non-Goals

**Goals:**
- Core SQLAlchemy 2.0 async models: User, Tenant, Role, Permission, UserRole, UserTenant
- Alembic migration creating all tables with proper constraints, indexes, FKs
- Repository base class with automatic tenant_id filtering
- Fine-grained RBAC system: Permission(`modulo:accion`), Role, UserRole, `require_permission` dependency
- Argon2id password hashing utility
- AES-256 encryption service for PII fields
- Soft delete mixin (deleted_at, is_deleted) + audit trail
- UUID primary keys, legajo as unique business field
- Comprehensive test suite (≥80% lines, ≥90% business rules)

**Non-Goals:**
- API endpoints for user/tenant/role management (C-03 auth, C-04 rbac)
- Authentication flows (JWT login, refresh, logout) — C-03
- Frontend components — C-21+
- Moodle integration — C-07+
- Academic domain models (alumnos, materias, comisiones) — C-06+

## Decisions

### 1. SQLAlchemy 2.0 Declarative + Async
**Decision**: Use `DeclarativeBase` with `Mapped`/`mapped_column`, async sessions throughout.
**Rationale**: Modern SQLAlchemy 2.0 pattern; type-safe; aligns with C-01's `core/database.py`.
**Alternative considered**: Classical mapping — rejected (verbose, less type-safe).

### 2. Tenant Scoping via Repository Base Class
**Decision**: `TenantScopedRepository[T]` base class with `tenant_id` filter applied in all query methods (`get`, `list`, `create`, `update`, `delete`).
**Rationale**: Enforces multi-tenancy at the data access layer; fail-safe (cannot forget to filter); testable.
**Alternative considered**: Middleware/tenant context — rejected (leaks into routers, harder to test, bypassable).

### 3. Soft Delete via Mixin + Query Filter
**Decision**: `SoftDeleteMixin` adds `deleted_at: Mapped[Optional[datetime]]`, `is_deleted: Mapped[bool]`. Base repository automatically filters `is_deleted == False`. Hard delete only via explicit `hard_delete()` method.
**Rationale**: Audit compliance (append-only); recoverable; simple query filter.
**Alternative considered**: Separate archive tables — rejected (complexity, JOIN overhead).

### 4. RBAC Permission Format: `modulo:accion`
**Decision**: Permission `name` = `modulo:accion` (e.g., `alumnos:read`, `comunicaciones:send`, `liquidaciones:approve`). Role aggregates permissions. UserRole links user+tenant+role. Endpoint protection via `require_permission("modulo:accion")` dependency.
**Rationale**: Explicit, auditable, matches KB rules (RN-XX). Fail-closed by default.
**Alternative considered**: String-based wildcards — rejected (ambiguous, harder to audit).

### 5. PII Encryption: AES-256-GCM via `cryptography`
**Decision**: `EncryptionService` with `encrypt(field: str) -> str` / `decrypt(encrypted: str) -> str`. Uses AES-256-GCM (authenticated encryption). Key derived from `ENCRYPTION_KEY` (32 bytes) in settings. Applied at model level via `@hybrid_property` or column transformer.
**Rationale**: Standard, authenticated encryption (tamper-proof); key rotation possible via key ID prefix.
**Alternative considered**: pgcrypto — rejected (portability, key management in DB).

### 6. Password Hashing: Argon2id via `argon2-cffi`
**Decision**: `PasswordService.hash(password: str) -> str`, `verify(password: str, hash: str) -> bool`. Uses `argon2.PasswordHasher()` with default params (memory=64MB, time=3, parallelism=4).
**Rationale**: OWASP recommended; memory-hard; future-proof.
**Alternative considered**: bcrypt — rejected (Argon2id is stronger).

### 7. UUID Identity + Legajo Business Field
**Decision**: All core models use `id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)`. `User.legajo: Mapped[str]` unique, indexed, NOT a credential.
**Rationale**: UUID prevents enumeration; legajo is business attribute per KB.
**Alternative considered**: Auto-increment integer — rejected (enumeration risk, not distributed-friendly).

### 8. Alembic Single Migration for Core Schema
**Decision**: One migration `create_core_schema` creating all 6 tables with FKs, indexes, constraints.
**Rationale**: Atomic schema creation; easier rollback; clean history.
**Alternative considered**: One migration per table — rejected (noise, dependency ordering).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Tenant filter bypass via raw SQL | Repository base is only data access path; code review enforces |
| Encryption key rotation | Key ID prefix in ciphertext; re-encrypt on read with old key |
| Argon2id DoS (memory-hard) | Rate-limit auth endpoints; monitor memory |
| Soft delete query pollution | Base repository auto-filters; explicit `include_deleted()` opt-in |
| RBAC permission explosion | Design-time permission catalog; `modulo:accion` namespace |

## Migration Plan

1. **Run migration**: `alembic upgrade head` (creates all core tables)
2. **Verify**: Check tables exist, indexes created, FKs enforced
3. **Seed**: Insert default `Permission` records for all `modulo:accion` from KB
4. **Rollback**: `alembic downgrade -1` (drops all 6 tables — destructive, dev only)

## Open Questions

1. **Default tenant for system users**: Should `User` exist without `UserTenant`? (Admin users may not belong to a tenant)
2. **Permission catalog source**: Generate from KB `05_reglas_de_negocio.md` RN-XX codes or maintain manually?
3. **Encryption key rotation schedule**: How often? Automated or manual?