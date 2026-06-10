## Context

C-02 implementó los modelos User, Tenant, Role, Permission, UserRole, UserTenant como entidades ORM. C-03 agregó autenticación JWT con `get_current_user` que resuelve identidad + tenant + roles desde el token. Sin embargo, los roles actualmente son solo nombres en el JWT — no hay un mecanismo que asocie permisos a roles y los verifique por endpoint.

Se necesita el sistema de autorización completo: tabla `rol_permiso` como catálogo administrable, seed de la matriz de capacidades, y un guard `require_permission()` que cada endpoint declare.

## Goals / Non-Goals

**Goals:**
- Modelos Rol, Permiso, RolPermiso como tablas en DB (catálogo administrable, no hardcode)
- Seed de 7 roles del dominio con ~20 permisos según matriz de §3.3
- Dependency `require_permission("modulo:accion")` que rechaza con 403 si falta el permiso
- Resolución de permisos efectivos por request: unión de roles del usuario, acotada por tenant
- Soporte de scope `(propio)`: el permiso solo aplica si el recurso pertenece al usuario
- Migración 002 con seed data
- Tests: 403 sin permiso, unión de roles, scope propio, catálogo administrable

**Non-Goals:**
- No se implementa UI de administración de roles/permisos — solo API si es necesaria
- No se implementa gestión de asignaciones de roles a usuarios (tabla UserRole ya existe de C-02)
- No se implementa vigencia temporal de asignaciones (ya existe de C-02, se reusa)
- No se implementa cache de permisos (resolución server-side en cada request)

## Decisions

### D1: Resolución de permisos en DB por request (sin cache en JWT)
- **Decisión**: Los permisos NO van en el JWT. Se resuelven en cada request consultando DB: roles del usuario → join con rol_permiso → permisos efectivos
- **Por qué**: Los permisos cambian cuando se modifica una asignación (ej: se vence el contrato de un profesor). Si estuvieran en el JWT, el cambio no se reflejaría hasta que expire el token. La latencia de una query de resolución es despreciable.
- **Alternativa considerada**: Meter permisos en claims del JWT — descartado por el problema de revocación en caliente.

### D2: Guard como dependency de FastAPI (no decorator)
- **Decisión**: `require_permission("modulo:accion")` es una función que devuelve una dependency de FastAPI
- **Por qué**: Las dependencies de FastAPI se ejecutan en el orden correcto (autenticación primero, luego autorización). Se pueden combinar con `Depends()` y son testeables unitariamente.
- **Alternativa considerada**: Decorator en el handler — no puede inspeccionar la request ni el usuario autenticado sin hacks.

### D3: Scope `(propio)` resuelto en la query (no en el guard)
- **Decisión**: `require_permission` solo verifica que el permiso existe en la matriz del usuario. El scope `(propio)` se resuelve en el Repository o Service al filtrar por `user_id` (ej: `atrasados:ver` con scope propio filtra donde `profesor_id = current_user.id`)
- **Por qué**: El guard no debe saber qué recurso se está consultando. El scope es una restricción de negocio que la capa de datos aplica. Separación de responsabilidades limpia.
- **Forma de uso**: `require_permission("atrasados:ver", scope="propio")` — el flag `scope` indica al service/repo que debe filtrar por el usuario autenticado. Si el permiso no tiene scope propio en la matriz, el flag se ignora.

### D4: Seed data como migración Alembic (no script aparte)
- **Decisión**: Los datos semilla (roles, permisos, rol_permiso) se insertan en la migración 002 como parte del `upgrade()`
- **Por qué**: Garantiza que la semilla existe en todas las instancias (local, test, prod). Una migración es el lugar correcto para datos de referencia.
- **Alternativa considerada**: Script seed.py separado — fácil de olvidar en deploy o en setup de test.

### D5: Permisos efectivos como función de servicio (no repository)
- **Decisión**: `PermissionService.get_effective_permissions(user_id)` en `services/permission_service.py` hace la lógica de unión de roles
- **Por qué**: La resolución de permisos es lógica de negocio (unión de conjuntos, chequeo de vigencia), no una query directa. El Service es la capa correcta.
- **Forma**: Recibe `user_id`, resuelve roles activos (UserRole vigente), cruza con RolPermiso, devuelve set de permisos `{"modulo:accion", ...}`

## Risks / Trade-offs

- **[Query de permisos por request] → Latencia adicional en cada endpoint.** La query es simple (2-3 joins indexados), el volumen de usuarios es bajo. Si en el futuro hay miles de requests/segundo, implementar cache con invalidación por evento (ej: al modificar una asignación, invalidar cache de permisos de ese usuario).
- **[Seed data en migración] → Cambiar la matriz requiere nueva migración.** Esto es correcto: los cambios en la matriz de permisos deben ser versionados y revisados como cualquier cambio de schema.
- **[Scope `(propio)` no verificado en el guard] → Un service podría olvidar aplicar el filtro.** Mitigación: tests específicos que validan que un usuario no ve datos de otro cuando el permiso es `(propio)`.

## Migration Plan

1. Crear migración 002 con tablas `rol`, `permiso`, `rol_permiso` + seed data
2. Ejecutar migración en DB de test
3. Ejecutar tests de permisos
4. En deploy: la migración corre automáticamente con Alembic

Rollback: `alembic downgrade -1` elimina las tablas (no hay datos de usuario que perder).

## Open Questions

- **PA-25**: El rol NEXO tiene permisos específicos que no están completamente definidos en la matriz. Dejar seed con los permisos mínimos necesarios y ajustar cuando se cierre la pregunta.
