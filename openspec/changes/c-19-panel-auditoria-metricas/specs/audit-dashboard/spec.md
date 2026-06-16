# Audit Dashboard

## ADDED Requirements

### Requirement: Dashboard returns aggregated metrics in a single response

The system SHALL expose a `GET /api/audit/dashboard` endpoint that returns four aggregated views in a single JSON response: acciones_por_dia, comunicaciones_por_docente, interacciones_por_docente_materia, and ultimas_acciones.

#### Scenario: Admin requests full dashboard
- **WHEN** an ADMIN user sends GET `/api/audit/dashboard`
- **THEN** the response SHALL contain 200 OK with four top-level keys: `acciones_por_dia`, `comunicaciones_por_docente`, `interacciones_por_docente_materia`, and `ultimas_acciones`

#### Scenario: Coordinator with scope propio requests dashboard
- **WHEN** a COORDINADOR user with scope `propio` in `auditoria:ver` sends GET `/api/audit/dashboard`
- **THEN** the response SHALL only include data for materias where the coordinator has an active Asignacion

#### Scenario: Finanzas requests dashboard
- **WHEN** a FINANZAS user sends GET `/api/audit/dashboard`
- **THEN** the response SHALL include data for all materias in the tenant (global scope)

#### Scenario: User without auditoria:ver permission
- **WHEN** a user without `auditoria:ver` sends GET `/api/audit/dashboard`
- **THEN** the response SHALL be 403 Forbidden

### Requirement: Dashboard actions_by_day aggregates AuditLog by date

The `acciones_por_dia` section SHALL contain an array of objects with `fecha` (date string) and `total` (integer count of actions), aggregated from `AuditLog` grouped by calendar date, ordered chronologically.

#### Scenario: Actions by day returns aggregated counts
- **WHEN** there are 10 audit entries on 2026-06-01 and 5 on 2026-06-02
- **THEN** the response SHALL include entries `{"fecha": "2026-06-01", "total": 10}` and `{"fecha": "2026-06-02", "total": 5}`

#### Scenario: Empty day range returns empty array
- **WHEN** there are no audit entries in the selected date range
- **THEN** `acciones_por_dia` SHALL be an empty array

### Requirement: Dashboard comunicaciones_por_docente shows communication state distribution

The `comunicaciones_por_docente` section SHALL aggregate `Comunicacion` records grouped by `enviado_por` (docente), counting records per `estado` (Pendiente, Enviando, Enviado, Error, Cancelado), including docente name.

#### Scenario: Communications grouped by docente
- **WHEN** docente A has 10 sent and 2 error communications
- **THEN** the response SHALL include an entry with `docente_id`, `docente_nombre`, `enviado: 10`, `error: 2`, and 0 for remaining states

#### Scenario: Docente with no communications is not listed
- **WHEN** a docente has zero Comunicacion records
- **THEN** that docente SHALL NOT appear in `comunicaciones_por_docente`

### Requirement: Dashboard interacciones_por_docente_materia shows detailed interaction metrics

The `interacciones_por_docente_materia` section SHALL aggregate `AuditLog` records grouped by `actor_id` (docente) and `materia_id`, with a breakdown of action counts per type, plus docente and materia names.

#### Scenario: Interactions grouped by docente and materia
- **WHEN** docente A performed 5 CALIFICACIONES_IMPORTAR and 3 COMUNICACION_ENVIAR actions on materia X
- **THEN** the response SHALL include `{"docente_id": <id>, "materia_id": <id>, "total_acciones": 8, "acciones": {"CALIFICACIONES_IMPORTAR": 5, "COMUNICACION_ENVIAR": 3}}`

#### Scenario: Materia with no audit entries omitted
- **WHEN** a materia has no audit entries
- **THEN** it SHALL NOT appear in `interacciones_por_docente_materia`

### Requirement: Dashboard ultimas_acciones returns recent log entries

The `ultimas_acciones` section SHALL return the most recent `AuditLog` entries ordered by `fecha_hora DESC`, with a default limit of 200 records and configurable via `limit` query parameter (1-200).

#### Scenario: Default limit returns 200 records
- **WHEN** there are 500 audit entries and no limit parameter is provided
- **THEN** the response SHALL contain exactly 200 entries

#### Scenario: Custom limit parameter
- **WHEN** `?limit=50` is provided
- **THEN** the response SHALL contain exactly the 50 most recent entries

#### Scenario: Limit exceeds maximum
- **WHEN** `?limit=500` is provided
- **THEN** the response SHALL cap at 200 entries (maximum)

### Requirement: Dashboard accepts optional date range filter

The dashboard endpoint SHALL accept optional `desde` and `hasta` query parameters (ISO 8601 date strings) to filter all four sections to a date range.

#### Scenario: Date range filter applied
- **WHEN** `?desde=2026-06-01&hasta=2026-06-15` is provided
- **THEN** all four response sections SHALL only include data within that date range

#### Scenario: Invalid date format
- **WHEN** an invalid date string is provided as `desde` or `hasta`
- **THEN** the response SHALL be 422 Unprocessable Entity

### Requirement: Dashboard accepts optional materia_id filter

The dashboard endpoint SHALL accept an optional `materia_id` query parameter to filter all sections to a single materia.

#### Scenario: Filter by materia
- **WHEN** `?materia_id=<uuid>` is provided
- **THEN** all four response sections SHALL only include data for that materia

### Requirement: Dashboard responses include last 200 entries by default

The `ultimas_acciones` array SHALL default to 200 entries when no explicit `limit` is provided, supporting the F9.1 requirement of "máximo configurable; defecto 200 registros".

#### Scenario: Dashboard default limit is 200
- **WHEN** GET `/api/audit/dashboard` is called without a limit parameter
- **THEN** `ultimas_acciones` SHALL contain at most 200 entries
