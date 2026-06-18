## ADDED Requirements

### Requirement: Modificar vigencia general del equipo
El sistema SHALL permitir actualizar las fechas de vigencia de todas las asignaciones de un equipo en una sola operación.

#### Scenario: Modificación exitosa
- **WHEN** un COORDINADOR envía PUT `/api/v1/equipos/{dictado_id}/vigencia` con `{ desde: "2026-03-01", hasta: "2026-07-31" }`
- **THEN** retorna 200 con la cantidad de asignaciones actualizadas
- **AND** todas las asignaciones de ese dictado tienen las nuevas fechas

#### Scenario: Dictado sin asignaciones
- **WHEN** se modifica la vigencia de un dictado sin asignaciones
- **THEN** retorna 200 con `actualizadas: 0`

#### Scenario: Fecha desde posterior a hasta
- **WHEN** se envía `desde` posterior a `hasta`
- **THEN** retorna 422 con error de validación

#### Scenario: Sin permisos de equipos:asignar
- **WHEN** un TUTOR intenta modificar vigencia
- **THEN** retorna 403

### Requirement: Auditoría de modificación de vigencia
El sistema SHALL registrar cada modificación de vigencia en el audit log.

#### Scenario: Audit log generado
- **WHEN** se completa una modificación de vigencia exitosamente
- **THEN** se crea un audit log con `accion = "ASIGNACION_MODIFICAR"`
- **AND** el detalle incluye `dictado_id`, `desde` nuevo, `hasta` nuevo, cantidad de asignaciones afectadas
