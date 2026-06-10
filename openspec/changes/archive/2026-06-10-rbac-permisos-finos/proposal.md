## Why

C-03 implementó autenticación (verificar QUIÉN es el usuario), pero sin autorización cualquier usuario autenticado puede hacer cualquier cosa. Necesitamos RBAC con permisos finos (`modulo:accion`) para controlar QUÉ puede hacer cada usuario según sus roles, su tenant y la vigencia de sus asignaciones.

## What Changes

- Modelos `Rol`, `Permiso`, `RolPermiso` — catálogo administrable como datos (no hardcodeado)
- Seed de 7 roles del dominio: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS
- Seed de ~20 permisos `modulo:accion` con la matriz de capacidades de `03_actores_y_roles.md` §3.3
- Dependency `require_permission("modulo:accion")` — cada endpoint declara su permiso; sin él → 403
- Resolución server-side de permisos efectivos por request (unión de roles, acotada por tenant y vigencia)
- Soporte de scope `(propio)` — permiso que solo aplica sobre datos propios del usuario
- Migración 002: `rol`, `permiso`, `rol_permiso` + seed data

## Capabilities

### New Capabilities
- `rbac-core`: Modelos Rol, Permiso, RolPermiso con seed de 7 roles y matriz completa de permisos; dependency `require_permission()` que valida contra la DB; resolución de permisos efectivos por request (unión de roles del usuario)
- `scope-propio`: Mecanismo para permisos con alcance `(propio)` — el permiso solo aplica si el recurso pertenece al usuario que hace la request (ej: PROFESOR solo ve sus propios alumnos, no los de otros)

### Modified Capabilities
- `user-auth` (de C-03): El JWT ya incluye `roles` en claims. Ahora los roles se usan para resolver permisos efectivos server-side. No cambian claims del JWT.

## Impact

- **backend/app/models/** — Nuevos modelos `role.py`, `permission.py`, `role_permission.py` (ya existen parcialmente de C-02, se expanden)
- **backend/app/core/permissions.py** — Nueva lógica de resolución de permisos + seed data
- **backend/app/core/dependencies.py** — Nueva dependency `require_permission(permiso)` que usa get_current_user para verificar
- **backend/app/schemas/** — Posibles schemas para administración de roles/permisos
- **backend/app/services/** — Posible `permission_service.py` para lógica de resolución
- **backend/alembic/** — Migración 002: rol, permiso, rol_permiso + seed data
- **C-03 `get_current_user`** — Se actualiza para exponer los permisos resueltos (no solo roles)
