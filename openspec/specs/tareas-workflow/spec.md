## ADDED Requirements

### Requirement: Crear tarea con asignación
El sistema SHALL permitir a usuarios con permiso `tareas:admin` (COORDINADOR, ADMIN) crear una nueva tarea especificando: `asignado_a` (UUID, requerido), `descripcion` (texto, requerido), `materia_id` (UUID, opcional), `contexto_id` (UUID, opcional).
El campo `asignado_por` SHALL asignarse automáticamente al usuario autenticado que crea la tarea.
El `estado` inicial SHALL ser `Pendiente`.

#### Scenario: Creación exitosa por COORDINADOR
- **WHEN** un COORDINADOR envía POST /api/v1/tareas con `asignado_a`, `descripcion` y opcionales
- **THEN** el sistema retorna 201 con la tarea creada, `asignado_por` igual al COORDINADOR, `estado` = "Pendiente"

#### Scenario: Creación rechazada por PROFESOR sin permiso admin
- **WHEN** un PROFESOR (solo `tareas:gestionar`) intenta POST /api/v1/tareas
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: Creación con asignado_a inexistente
- **WHEN** se crea una tarea con `asignado_a` que no corresponde a un usuario válido del tenant
- **THEN** el sistema retorna 422 con error de validación

#### Scenario: Creación sin descripción
- **WHEN** se crea una tarea sin `descripcion`
- **THEN** el sistema retorna 422 con error de validación

### Requirement: Transiciones de estado forward-only
El sistema SHALL validar que las transiciones de estado de una tarea solo ocurran hacia adelante en el ciclo: Pendiente → EnProgreso → Resuelta → Cancelada.
Transiciones inválidas SHALL devolver error 422.
Solo COORDINADOR/ADMIN (`tareas:admin`) pueden cambiar estado de cualquier tarea.
PROFESOR/TUTOR (`tareas:gestionar`) solo pueden cambiar estado de tareas donde `asignado_a` = usuario autenticado.

#### Scenario: Transición válida Pendiente → EnProgreso
- **WHEN** el asignado actualiza estado a "EnProgreso"
- **THEN** el sistema retorna 200 con estado actualizado

#### Scenario: Transición inválida Pendiente → Cancelada por PROFESOR
- **WHEN** un PROFESOR intenta cambiar estado de Pendiente a Cancelada
- **THEN** el sistema retorna 422 (solo COORDINADOR/ADMIN pueden cancelar)

#### Scenario: Transición inválida retroceso (EnProgreso → Pendiente)
- **WHEN** se intenta volver de "EnProgreso" a "Pendiente"
- **THEN** el sistema retorna 422 con descripción del error

#### Scenario: PROFESOR no puede cambiar estado de tarea ajena
- **WHEN** un PROFESOR intenta PUT /api/v1/tareas/{id} donde `asignado_a` != current_user
- **THEN** el sistema retorna 403 Forbidden

#### Scenario: Transición Cancelada desde cualquier estado por COORDINADOR
- **WHEN** un COORDINADOR envía estado "Cancelada" desde Pendiente o EnProgreso o Resuelta
- **THEN** el sistema retorna 200 con estado "Cancelada"

### Requirement: Reasignar tarea
El sistema SHALL permitir a usuarios con `tareas:admin` modificar el campo `asignado_a` de una tarea existente.
El `asignado_por` original NO cambia (trazabilidad del creador original).
La descripción y materia_id pueden actualizarse junto con la reasignación.

#### Scenario: Reasignación exitosa por COORDINADOR
- **WHEN** un COORDINADOR hace PUT /api/v1/tareas/{id} cambiando `asignado_a`
- **THEN** el sistema retorna 200 con el nuevo `asignado_a` y el `asignado_por` original intacto

#### Scenario: Reasignación rechazada por PROFESOR
- **WHEN** un PROFESOR intenta cambiar `asignado_a`
- **THEN** el sistema retorna 403 Forbidden

### Requirement: Soft delete de tarea
El sistema SHALL permitir soft delete de tareas solo a usuarios con `tareas:admin`.
El borrado SHALL setear `deleted_at` (no eliminar físicamente).
Tareas eliminadas NO aparecen en listados por defecto.

#### Scenario: Soft delete exitoso por ADMIN
- **WHEN** un ADMIN hace DELETE /api/v1/tareas/{id}
- **THEN** el sistema retorna 204 y la tarea tiene `deleted_at` seteado

#### Scenario: Soft delete rechazado por PROFESOR
- **WHEN** un PROFESOR intenta DELETE /api/v1/tareas/{id}
- **THEN** el sistema retorna 403 Forbidden

### Requirement: Obtener detalle de tarea
El sistema SHALL exponer GET /api/v1/tareas/{id} que retorna el detalle completo de una tarea incluyendo comentarios.
PROFESOR/TUTOR solo pueden ver tareas donde `asignado_a` = usuario autenticado.

#### Scenario: COORDINADOR ve cualquier tarea
- **WHEN** un COORDINADOR hace GET /api/v1/tareas/{id} con ID de cualquier tarea del tenant
- **THEN** el sistema retorna 200 con el detalle completo

#### Scenario: PROFESOR ve tarea propia
- **WHEN** un PROFESOR hace GET /api/v1/tareas/{id} donde `asignado_a` = su ID
- **THEN** el sistema retorna 200 con el detalle

#### Scenario: PROFESOR no puede ver tarea ajena
- **WHEN** un PROFESOR hace GET /api/v1/tareas/{id} donde `asignado_a` != su ID
- **THEN** el sistema retorna 404 (no revela existencia de tareas ajenas)
