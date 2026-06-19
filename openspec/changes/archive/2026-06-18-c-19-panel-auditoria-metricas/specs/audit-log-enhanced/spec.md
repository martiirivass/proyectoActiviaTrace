# Audit Log Enhanced

## ADDED Requirements

### Requirement: Log endpoint accepts materia_id filter

The existing `GET /api/audit/log` endpoint SHALL accept an optional `materia_id` query parameter to filter results by materia.

#### Scenario: Filter log by materia_id
- **WHEN** `?materia_id=<uuid>` is provided in GET `/api/audit/log`
- **THEN** the response SHALL only include AuditLog entries with matching materia_id

#### Scenario: Invalid materia_id UUID
- **WHEN** an invalid UUID string is provided as `materia_id`
- **THEN** the response SHALL be 422 Unprocessable Entity

#### Scenario: Materia_id with no matches
- **WHEN** no entries match the given materia_id
- **THEN** the response SHALL be an empty array with 200 OK

### Requirement: Log endpoint respects scope propio for COORDINADOR

When a COORDINADOR user has `auditoria:ver` with scope `propio`, the log endpoint SHALL automatically filter results to only include materias where the user has active asignaciones.

#### Scenario: Coordinator sees only own materias in log
- **WHEN** a COORDINADOR with scope `propio` sends GET `/api/audit/log`
- **THEN** the response SHALL only include entries for materias assigned to that coordinator

#### Scenario: Coordinator explicit materia_id within scope
- **WHEN** a COORDINADOR provides a `materia_id` that belongs to their assigned materias
- **THEN** the response SHALL filter to that materia (intersection of scope and param)

#### Scenario: Coordinator materia_id outside scope
- **WHEN** a COORDINADOR provides a `materia_id` NOT in their assigned materias
- **THEN** the response SHALL be an empty array (scope overrides)

### Requirement: Log endpoint limit increased to 200

The `limit` parameter for GET `/api/audit/log` SHALL accept values up to 200 (previously 50), with default remaining 50 for backward compatibility.

#### Scenario: Limit of 200 accepted
- **WHEN** `?limit=200` is provided
- **THEN** the response SHALL return up to 200 entries

#### Scenario: Default limit remains 50
- **WHEN** no limit parameter is provided
- **THEN** the response SHALL return at most 50 entries (backward compatible)

#### Scenario: Limit exceeds maximum returns 422
- **WHEN** `?limit=201` is provided
- **THEN** the response SHALL be 422 Unprocessable Entity

### Requirement: Log endpoint supports existing filters

The existing filters (`accion`, `actor_id`, `desde`, `hasta`, `offset`, `limit`) SHALL continue working as before.

#### Scenario: Existing filter backward compatibility
- **WHEN** `?accion=CALIFICACIONES_IMPORTAR&actor_id=<uuid>&desde=2026-06-01` is provided
- **THEN** the response SHALL filter by all provided parameters as before
