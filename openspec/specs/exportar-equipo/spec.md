## ADDED Requirements

### Requirement: Exportar equipo a CSV
El sistema SHALL permitir exportar el detalle de asignaciones de un equipo como archivo CSV descargable.

#### Scenario: Exportación exitosa
- **WHEN** un COORDINADOR envía GET `/api/v1/equipos/{dictado_id}/exportar`
- **THEN** retorna 200 con `Content-Type: text/csv`
- **AND** el CSV incluye columnas: docente, rol, materia, carrera, cohorte, desde, hasta, estado_vigencia

#### Scenario: Sin asignaciones en el equipo
- **WHEN** se exporta un dictado sin asignaciones
- **THEN** retorna 200 con CSV que solo contiene los encabezados

#### Scenario: Permiso requerido
- **WHEN** un TUTOR intenta exportar un equipo
- **THEN** retorna 403
