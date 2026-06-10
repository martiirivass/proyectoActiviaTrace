## ADDED Requirements

### Requirement: Clonar equipo docente entre períodos
El sistema SHALL permitir duplicar las asignaciones vigentes de un equipo origen hacia un destino, respetando RN-12.

#### Scenario: Clonación exitosa
- **WHEN** un COORDINADOR envía POST `/api/v1/equipos/clonar` con `{ dictado_origen_id, dictado_destino_id }`
- **THEN** retorna 201 con la lista de asignaciones clonadas
- **AND** se duplicaron todas las asignaciones vigentes del origen
- **AND** las copias tienen `dictado_id = dictado_destino_id`
- **AND** las copias tienen las fechas `desde`/`hasta` del dictado destino
- **AND** las copias conservan `usuario_id`, `rol` y `responsable_id` del origen

#### Scenario: Destino ya tiene asignaciones
- **WHEN** el dictado destino ya tiene asignaciones previas
- **THEN** retorna 409 con mensaje de conflicto
- **AND** no se crea ninguna asignación

#### Scenario: Clonación forzada con destino ocupado
- **WHEN** se envía con `force: true` y el destino ya tiene asignaciones
- **THEN** retorna 201 con las nuevas asignaciones
- **AND** las asignaciones existentes del destino se conservan

#### Scenario: Origen sin asignaciones vigentes
- **WHEN** el dictado origen no tiene asignaciones vigentes
- **THEN** retorna 200 con lista vacía
- **AND** no se crea ninguna asignación

#### Scenario: Dictado origen no existe
- **WHEN** el `dictado_origen_id` no existe
- **THEN** retorna 404

#### Scenario: Sin permisos de equipos:asignar
- **WHEN** un PROFESOR intenta clonar
- **THEN** retorna 403

### Requirement: Auditoría de clonación
El sistema SHALL registrar cada clonación en el audit log.

#### Scenario: Audit log generado
- **WHEN** se completa una clonación exitosamente
- **THEN** se crea un audit log con `accion = "ASIGNACION_MODIFICAR"`
- **AND** el detalle incluye `dictado_origen_id`, `dictado_destino_id`, cantidad de asignaciones clonadas
