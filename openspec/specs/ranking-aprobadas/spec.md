## ADDED Requirements

### Requirement: Sistema genera ranking de actividades aprobadas (RN-09)

El sistema SHALL generar un ranking descendente por cantidad de actividades aprobadas por alumno. Solo incluye alumnos con al menos una actividad aprobada (RN-09).

#### Scenario: Ranking ordena descendente por aprobadas
- **WHEN** se consulta ranking para una materia donde Alumno A tiene 5 aprobadas, Alumno B tiene 3 aprobadas, Alumno C tiene 1 aprobada
- **THEN** el ranking retorna: Alumno A (5), Alumno B (3), Alumno C (1) en ese orden

#### Scenario: Alumno sin actividades aprobadas no aparece en ranking
- **WHEN** se consulta ranking para una materia donde Alumno D tiene 0 actividades aprobadas
- **THEN** el Alumno D NO aparece en el ranking

#### Scenario: Empate en cantidad de aprobadas se ordena alfabéticamente
- **WHEN** Alumno A y Alumno B tienen ambos 4 actividades aprobadas
- **THEN** aparecen ordenados alfabéticamente por apellido y nombre

#### Scenario: Ranking incluye datos del alumno
- **WHEN** se consulta ranking
- **THEN** cada entrada incluye: nombre completo del alumno, email, comisión, cantidad de aprobadas, total de actividades, y porcentaje de aprobación

### Requirement: Ranking respeta filtro por materia

El sistema SHALL permitir consultar el ranking de una materia específica.

#### Scenario: Ranking filtrado por materia
- **WHEN** se consulta ranking con `materia_id` específico
- **THEN** el ranking solo incluye alumnos con calificaciones en esa materia
