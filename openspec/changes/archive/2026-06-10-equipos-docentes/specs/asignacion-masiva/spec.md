## ADDED Requirements

### Requirement: Asignación masiva de docentes
El sistema SHALL permitir asignar múltiples docentes a un mismo contexto académico en una sola operación atómica.

#### Scenario: Asignación masiva exitosa
- **WHEN** un COORDINADOR envía POST `/api/v1/equipos/masiva` con `{ dictado_id, rol, desde, hasta, usuario_ids: [uuid1, uuid2, uuid3] }`
- **THEN** retorna 201 con la lista de asignaciones creadas
- **AND** se creó una asignación por cada `usuario_id` en la lista
- **AND** todas comparten el mismo `dictado_id`, `rol`, `desde` y `hasta`

#### Scenario: Usuario duplicado en la lista
- **WHEN** la lista `usuario_ids` contiene el mismo UUID más de una vez
- **THEN** retorna 422 con detalle del duplicado
- **AND** no se crea ninguna asignación

#### Scenario: Usuario_id inválido
- **WHEN** la lista contiene un `usuario_id` que no existe
- **THEN** retorna 422 con detalle del primer UUID inválido
- **AND** no se crea ninguna asignación

#### Scenario: Rol inválido
- **WHEN** se envía con un `rol` no reconocido
- **THEN** retorna 422 con error de validación

#### Scenario: Sin permisos de equipos:asignar
- **WHEN** un PROFESOR intenta la asignación masiva
- **THEN** retorna 403

### Requirement: Auditoría de asignación masiva
El sistema SHALL registrar cada asignación masiva en el audit log.

#### Scenario: Audit log generado
- **WHEN** se completa una asignación masiva exitosamente
- **THEN** se crea un audit log con `accion = "ASIGNACION_MODIFICAR"`
- **AND** el detalle incluye `dictado_id`, `rol`, cantidad de docentes asignados y `usuario_id` del operador
