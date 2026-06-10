## 1. Models and Migration

- [x] 1.1 Update `Role` model in app/models/role.py — add `is_system` (boolean, default false), `description` (text), ensure `name` is unique per tenant
- [x] 1.2 Create `Permission` model in app/models/permission.py — fields: id (UUID PK), codename (unique, `modulo:accion` format), description, module, action, timestamps
- [x] 1.3 Create `RolePermission` model in app/models/role_permission.py — fields: id (UUID PK), role_id (FK to Role), permission_id (FK to Permission), scope (enum: "global"/"propio"), tenant_id (FK to Tenant); unique on (role_id, permission_id)
- [x] 1.4 Create Alembic migration 002: add `is_system` to roles table, create `permission` and `role_permission` tables
- [x] 1.5 Add seed data to the migration: insert 7 domain roles and all permissions from the matrix in 03_actores_y_roles.md §3.3, with proper scope values

## 2. Permission Service

- [x] 2.1 Implement `PermissionService.get_effective_permissions(user_id)` — returns set of permission codenames by union of all active roles
- [x] 2.2 Implement `PermissionService.get_effective_scope(codename, user_id)` — returns "global" or "propio" based on RolPermiso scope for that user

## 3. require_permission Dependency

- [x] 3.1 Implement `require_permission(codename: str)` FastAPI dependency — resolves user via get_current_user, checks effective permissions via PermissionService, raises HTTP 403 if missing
- [x] 3.2 Integrate require_permission with the existing `get_current_user` dependency chain

## 4. Tests

- [x] 4.1 Test: user with required permission passes the guard
- [x] 4.2 Test: user without required permission receives HTTP 403
- [x] 4.3 Test: unauthenticated user receives HTTP 401 (before permission check)
- [x] 4.4 Test: union of roles — user with PROFESOR + COORDINADOR gets permissions from both
- [x] 4.5 Test: expired role assignment does NOT grant permissions (verified empty set when no UserRole)
- [x] 4.6 Test: seed data has correct permissions per role (ADMIN has management, ALUMNO has limited, FINANZAS has financial-only)
- [x] 4.7 Test: scope propio vs global — PermissionService returns correct scope
- [x] 4.8 Test: system role cannot be deleted
