## Context

activia-trace opera como capa de orquestación multi-tenant sobre Moodle. Cada tenant (institución educativa) tiene aislamiento total de datos. El modelo de datos del dominio (KB `04_modelo_de_datos.md`) define entidades con `tenant_id` obligatorio y soft-delete. La arquitectura (KB `08_arquitectura_propuesta.md` §4, §6; `docs/ARQUITECTURA.md` §6, §8) exige:

- **Row-level multi-tenancy** (ADR-002): todo query filtra por `tenant_id` por defecto; un query sin scope falla en code review
- **Soft delete transversal**: nunca borrado físico; `deleted_at` timestamp + filtro `WHERE deleted_at IS NULL`
- **PII cifrada en reposo**: AES-256-GCM para DNI, CUIL, CBU, email; Argon2id para passwords
- **Identidad desde JWT verificado**: nunca de parámetros (regla de oro, KB `07_flujos_principales.md` FL-01)
- **Migración por cambio de schema**: una migración Alembic por change

Estado actual: C-01 (foundation) entregado con FastAPI skeleton, DB async, health-check, Docker, OTel. No hay modelos de dominio, ni repos, ni cifrado.

## Goals / Non-Goals

**Goals:**
- Modelo `Tenant` raíz + mixin base reutilizable (`id` UUID, `tenant_id`, timestamps, soft-delete)
- `BaseRepository` que **inyecta `tenant_id` en todo query** (create, get, list, update, soft-delete) y expone `include_deleted` solo para auditoría
- `EncryptionService` (AES-256-GCM) + `PasswordService` (Argon2id) como singletons configurables desde `Settings`
- Modelos de identidad: `User` (PII cifrada), `Role`, `Permission` (`modulo:accion`), `UserRole`, `UserTenant`
- Migración Alembic 001 idempotente que crea todas las tablas con FKs, índices, constraints
- Tests: aislamiento cross-tenant, soft-delete, cifrado round-trip, mixin behavior

**Non-Goals:**
- Endpoints HTTP (auth en C-03, RBAC en C-04)
- Seed de roles/permisos base (en C-04 migración 002)
- Integración Moodle / N8N (C-09)
- Frontend (C-21+)

## Decisions

### 1. Mixin único vs mixins separados
**Decisión**: Un solo `TenantScopedMixin` (UUID PK + `tenant_id` FK + timestamps + `deleted_at`).
**Razón**: Todas las entidades de dominio lo necesitan; evita herencia múltiple y diamond problem. `UserRole` y `UserTenant` son tablas de enlace sin soft-delete → heredan solo `UUIDMixin` + `tenant_id` explícito.

### 2. Tenant-scope en Repository: ¿dónde vive el `tenant_id`?
**Decisión**: `BaseRepository.__init__(self, session, tenant_id: UUID)` — el `tenant_id` viene del request context (dependency `get_tenant` en C-03) y se inyecta al instanciar el repo en el Service.
**Razón**: Fuerza el scope en **cada método** (`create`, `get`, `list`, `update`, `delete`). Un repo sin `tenant_id` no compila. `include_deleted=True` solo para auditoría/admin.

### 3. Cifrado AES-256-GCM vs Fernet vs pgcrypto
**Decisión**: `cryptography.hazmat.primitives.ciphers.aead.AESGCM` — clave de 32 bytes desde `ENCRYPTION_KEY` (base64), nonce aleatorio 12 bytes por cifrado, tag de autenticación incluido.
**Razón**: Estándar, rápido, autentica integridad (tamper-evident), nonce único por valor evita reutilización. Fernet añade overhead; pgcrypto acopla a Postgres.

### 4. Argon2id para passwords
**Decisión**: `argon2.PasswordHasher()` con defaults seguros (time_cost=3, memory_cost=65536, parallelism=4).
**Razón**: Ganador PHC 2015, resistente a GPU/ASIC, configurable. `bcrypt` queda como fallback solo si migración legacy.

### 5. Permission naming: `modulo:accion`
**Decisión**: String único `"materias:crear"`, `"calificaciones:importar"`, `"comunicacion:aprobar"`. Tabla `Permission` con `name` UNIQUE + comentario descriptivo.
**Razón**: Legible, administrado por datos (no código), permite `(propio)` scope dinámico en C-04.

### 6. Alembic: una migración por change
**Decisión**: Migración `14e42736490b_initial_models.py` crea TODO: tenant, user, role, permission, user_role, user_tenant. Nombrada `001` por convención.
**Razón**: Atómico, rollback simple, trazabilidad 1:1 con change OPSX.

### 7. Soft-delete: `deleted_at` vs `is_deleted` boolean
**Decisión**: `deleted_at` TIMESTAMP WITH TIME ZONE (nullable) + propiedad híbrida `is_deleted` → `deleted_at IS NOT NULL`.
**Razón**: Permite saber **cuándo** se borró (auditoría), indexable, compatible con `BaseRepository.soft_delete()` que setea `datetime.utcnow()`.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| `tenant_id` se olvida en un query manual (raw SQL) | Code review obligatorio: grep `session.execute` sin `tenant_id` → reject. Linter futuro. |
| Clave `ENCRYPTION_KEY` rotada → datos ilegibles | Documentar procedimiento de re-cifrado masivo (script admin). No rotar en producción sin plan. |
| Argon2id muy lento en CPU bajo | Defaults conservadores; ajustable via `Settings` si benchmarks lo exigen. |
| `UserRole` / `UserTenant` sin soft-delete → huérfanos lógicos | Son tablas de enlace; vigencia se maneja con `desde`/`hasta` en `Asignacion` (C-07). No requieren soft-delete. |
| Migración 001 no idempotente en re-ejecución | `IF NOT EXISTS` en `CREATE TABLE` + `op.get_bind().inspect()` checks. Test de migración limpia en CI. |

## Migration Plan

1. `alembic upgrade head` (aplica 001) — crea tablas, FKs, índices, constraints
2. Verificar con `alembic history` y `SELECT * FROM alembic_version`
3. Rollback: `alembic downgrade -1` (elimina tablas en orden inverso por FKs)
4. Seed de datos (roles/permisos) en C-04 migración 002

## Open Questions

- **PA-25** (KB `10_preguntas_abiertas.md`): Semántica exacta del rol `NEXO` — ¿es un rol más o tiene permisos transversales especiales? Resolver antes de C-04 seed.
- **PA-01**: Catálogo `Materia` vs `InstanciaDictado` (ADR-006) — afecta modelo en C-06. Confirmar con stakeholder antes de C-06.