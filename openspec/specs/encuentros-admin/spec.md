## ADDED Requirements

### Requirement: Vista admin transversal de encuentros (F6.5)
El sistema SHALL exponer un endpoint para que COORDINADOR y ADMIN consulten todos los encuentros del tenant.
El endpoint SHALL ser `GET /api/v1/encuentros/admin` con filtros opcionales: `materia_id`, `fecha_desde`, `fecha_hasta`, `estado`, `asignacion_id`.
Los resultados SHALL incluir datos del slot (si existe), materia, y docente asignado.
La respuesta SHALL ser paginada con `offset` y `limit` (defecto 50, máximo 200).
Solo usuarios con rol COORDINADOR o ADMIN pueden acceder (validado además del permiso `encuentros:gestionar`).

#### Scenario: Consulta admin sin filtros
- **WHEN** un COORDINADOR envía GET `/api/v1/encuentros/admin`
- **THEN** el sistema devuelve todas las instancias del tenant paginadas
- **AND** cada item incluye materia_nombre, docente_nombre, fecha, hora, estado

#### Scenario: Consulta admin filtrada por materia y rango de fechas
- **WHEN** un ADMIN envía GET `/api/v1/encuentros/admin?materia_id=UUID&fecha_desde=2026-03-01&fecha_hasta=2026-03-31`
- **THEN** el sistema devuelve solo las instancias de esa materia en marzo 2026

#### Scenario: TUTOR no puede acceder a vista admin
- **WHEN** un TUTOR con permiso `encuentros:gestionar` envía GET `/api/v1/encuentros/admin`
- **THEN** el sistema responde 403 Forbidden
