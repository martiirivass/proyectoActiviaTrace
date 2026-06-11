## ADDED Requirements

### Requirement: Generar bloque HTML para LMS (F6.4)
El sistema SHALL generar un bloque HTML embebible con el cronograma de encuentros de una materia.
El endpoint SHALL ser `GET /api/v1/encuentros/{materia_id}/exportar-html`.
EL contenido SHALL incluir SOLO instancias con estado `Programado` o `Realizado` (excluye `Cancelado`).
El HTML SHALL ser una tabla con columnas: Fecha, Hora, Título, Encuentro (link al meet_url), Grabación (link al video_url si existe).
El bloque NO debe incluir estilos inline que puedan colisionar con el LMS; usa clases semánticas.
La respuesta SHALL tener `Content-Type: text/html; charset=utf-8`.

#### Scenario: Exportar HTML con instancias programadas y realizadas
- **WHEN** un PROFESOR envía GET `/api/v1/encuentros/{materia_id}/exportar-html`
- **AND** la materia tiene 3 instancias (2 Programadas, 1 Realizada con video_url, 1 Cancelada)
- **THEN** el sistema devuelve HTML con 3 filas (Programadas + Realizada, excluye Cancelada)
- **AND** la fila Realizada incluye enlace al video_url
- **AND** el Content-Type es text/html

#### Scenario: Exportar HTML vacío (sin instancias activas)
- **WHEN** un COORDINADOR envía GET `/api/v1/encuentros/{materia_id}/exportar-html`
- **AND** la materia no tiene instancias Programadas ni Realizadas
- **THEN** el sistema devuelve HTML con mensaje "No hay encuentros programados"
- **AND** la respuesta es 200 OK (no 404)
