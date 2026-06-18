## ADDED Requirements

### Requirement: Permiso `tareas:gestionar`
El sistema SHALL incluir el permiso `tareas:gestionar` en el catálogo de permisos RBAC.
Otorga las siguientes capacidades:
- Listar tareas donde `asignado_a` = usuario autenticado
- Ver detalle de tareas propias
- Actualizar estado de tareas propias (Pendiente → EnProgreso → Resuelta)
- Agregar comentarios a tareas propias

Roles que SHALL tener este permiso por defecto: PROFESOR, TUTOR, COORDINADOR, ADMIN.

#### Scenario: Seed incluye tareas:gestionar para roles docentes
- **WHEN** se consulta la matriz de permisos del tenant
- **THEN** PROFESOR, TUTOR, COORDINADOR, ADMIN tienen `tareas:gestionar`

### Requirement: Permiso `tareas:admin`
El sistema SHALL incluir el permiso `tareas:admin` en el catálogo de permisos RBAC.
Otorga todas las capacidades de `tareas:gestionar` más:
- Listar y ver cualquier tarea del tenant
- Crear tareas (asignar)
- Reasignar tareas (cambiar `asignado_a`)
- Cambiar estado a cualquier tarea (incluyendo Cancelada desde cualquier estado)
- Soft delete de tareas

Roles que SHALL tener este permiso por defecto: COORDINADOR, ADMIN.

#### Scenario: Seed incluye tareas:admin para coordinación
- **WHEN** se consulta la matriz de permisos del tenant
- **THEN** COORDINADOR y ADMIN tienen `tareas:admin`

### Requirement: Endpoints declaran permiso requerido
Cada endpoint del módulo SHALL declarar su permiso mínimo mediante `require_permission(...)`:
| Endpoint | Permiso |
|----------|---------|
| POST /api/v1/tareas | `tareas:admin` |
| GET /api/v1/tareas | `tareas:gestionar` |
| GET /api/v1/tareas/{id} | `tareas:gestionar` |
| PUT /api/v1/tareas/{id} | `tareas:gestionar` (scope propio) o `tareas:admin` (global) |
| DELETE /api/v1/tareas/{id} | `tareas:admin` |
| POST /api/v1/tareas/{id}/comentarios | `tareas:gestionar` |
| GET /api/v1/tareas/{id}/comentarios | `tareas:gestionar` |

#### Scenario: POST tareas sin tareas:admin retorna 403
- **WHEN** un usuario sin `tareas:admin` intenta POST /api/v1/tareas
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: GET tareas con tareas:gestionar funciona
- **WHEN** un usuario con `tareas:gestionar` hace GET /api/v1/tareas
- **THEN** el sistema retorna 200 con las tareas filtradas por su identidad
