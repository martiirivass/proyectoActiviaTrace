## ADDED Requirements

### Requirement: Agregar comentario a tarea
El sistema SHALL permitir a cualquier usuario con acceso a la tarea agregar comentarios (append-only).
Los comentarios SHALL contener: `texto` (texto, requerido), `autor_id` (UUID, automático desde sesión), `creado_at` (datetime, automático).
No SHALL existir endpoints de edición ni borrado de comentarios.

#### Scenario: Agregar comentario exitosamente
- **WHEN** un usuario autenticado con acceso a la tarea envía POST /api/v1/tareas/{id}/comentarios con `texto`
- **THEN** el sistema retorna 201 con el comentario creado, `autor_id` = usuario autenticado, `creado_at` = timestamp actual

#### Scenario: Comentario sin texto
- **WHEN** se envía POST /api/v1/tareas/{id}/comentarios sin `texto` o con texto vacío
- **THEN** el sistema retorna 422 con error de validación

#### Scenario: Comentario en tarea inexistente
- **WHEN** se envía POST /api/v1/tareas/{id}/comentarios con un ID de tarea que no existe
- **THEN** el sistema retorna 404

#### Scenario: Comentario en tarea de otro tenant
- **WHEN** se intenta comentar en una tarea de otro tenant
- **THEN** el sistema retorna 404 (aislamiento multi-tenant)

### Requirement: Listar comentarios de una tarea
El sistema SHALL exponer GET /api/v1/tareas/{id}/comentarios que retorna todos los comentarios de la tarea ordenados por `creado_at` ascendente.
Los comentarios de tareas soft-deleteadas NO se listan.

#### Scenario: Listar comentarios de tarea existente
- **WHEN** se hace GET /api/v1/tareas/{id}/comentarios con ID válido
- **THEN** el sistema retorna 200 con un array de comentarios ordenados por fecha ascendente

#### Scenario: Listar comentarios de tarea sin comentarios
- **WHEN** se hace GET /api/v1/tareas/{id}/comentarios de una tarea sin comentarios
- **THEN** el sistema retorna 200 con un array vacío
