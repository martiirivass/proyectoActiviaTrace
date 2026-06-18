## ADDED Requirements

### Requirement: Registrar resultado de coloquio
El sistema SHALL exponer `POST /api/v1/evaluaciones/resultados` para que PROFESOR y COORDINADOR (permiso `coloquios:gestionar`) registren la nota final de un alumno en una convocatoria.
El body SHALL incluir: `evaluacion_id`, `alumno_id`, `nota_final` (texto — numérica o cualitativa), `estado: "Borrador"`.
Si ya existe un resultado para ese alumno en esa evaluacion, SHALL responder 409 (usar PATCH para actualizar).

#### Scenario: Registrar nota final
- **WHEN** un PROFESOR envía POST `/api/v1/evaluaciones/resultados` con evaluacion_id, alumno_id y nota_final="8"
- **THEN** el sistema crea el resultado en estado Borrador
- **AND** responde 201

#### Scenario: Resultado duplicado
- **WHEN** un COORDINADOR intenta registrar un resultado ya existente para el mismo alumno y evaluacion
- **THEN** el sistema responde 409 Conflict

### Requirement: Actualizar resultado (F7.5)
El sistema SHALL exponer `PATCH /api/v1/evaluaciones/resultados/{id}` para actualizar `nota_final` y/o `estado`.
La transición de estado SHALL ser: Borrador → Definitivo (no se puede volver a Borrador).
Cuando el estado pasa a Definitivo, SHALL auditar `RESULTADO_REGISTRAR`.
Solo PROFESOR y COORDINADOR con permiso `coloquios:gestionar` pueden actualizar.

#### Scenario: Pasar resultado a Definitivo
- **WHEN** un PROFESOR envía PATCH `/api/v1/evaluaciones/resultados/{id}` con `{"estado": "Definitivo"}`
- **THEN** el sistema actualiza el estado
- **AND** audita la operación
- **AND** responde 200

#### Scenario: Rechazar cambio de Definitivo a Borrador
- **WHEN** un COORDINADOR intenta cambiar un resultado Definitivo a Borrador
- **THEN** el sistema responde 422

### Requirement: Registro académico consolidado (HU-33)
El sistema SHALL exponer `GET /api/v1/evaluaciones/resultados` para consultar el registro académico consolidado.
Filtros: `evaluacion_id`, `materia_id`, `cohorte_id`, `estado` (Borrador|Definitivo).
La respuesta SHALL ser paginada e incluir datos del alumno (nombre, apellido), materia, instancia, nota_final y estado.
Accesible para COORDINADOR y ADMIN.

#### Scenario: Consultar resultados de una convocatoria
- **WHEN** un COORDINADOR envía GET `/api/v1/evaluaciones/resultados?evaluacion_id=UUID`
- **THEN** el sistema devuelve todos los resultados de esa convocatoria paginados
