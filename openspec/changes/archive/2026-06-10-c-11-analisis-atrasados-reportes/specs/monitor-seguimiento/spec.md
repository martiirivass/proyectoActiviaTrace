## ADDED Requirements

### Requirement: Monitor de seguimiento muestra estado de alumnos asignados (TUTOR/PROFESOR)

El sistema SHALL proveer una vista filtrable del estado de actividades de los alumnos asignados al TUTOR o PROFESOR que consulta (F2.8).

#### Scenario: Seguimiento solo muestra alumnos del usuario
- **WHEN** un TUTOR consulta el monitor de seguimiento
- **THEN** solo se retornan alumnos que están dentro de las asignaciones del TUTOR (scope propio)

#### Scenario: Seguimiento filtra por alumno
- **WHEN** se consulta seguimiento con `alumno_id`
- **THEN** solo se retorna el estado de ese alumno específico

#### Scenario: Seguimiento filtra por correo
- **WHEN** se consulta seguimiento con `email = "alumno@example.com"`
- **THEN** solo se retorna el alumno con ese email

#### Scenario: Seguimiento filtra por comisión
- **WHEN** se consulta seguimiento con `comision`
- **THEN** solo se retornan alumnos de esa comisión

#### Scenario: Seguimiento filtra por regional
- **WHEN** se consulta seguimiento con `regional`
- **THEN** solo se retornan alumnos de esa regional

#### Scenario: Seguimiento filtra por actividad específica
- **WHEN** se consulta seguimiento con `actividad = "TP1"`
- **THEN** el estado se muestra filtrado a esa actividad específica

#### Scenario: Seguimiento filtra por mínimo de actividad cumplida
- **WHEN** se consulta seguimiento con `min_actividades = 3`
- **THEN** solo se retornan alumnos con al menos 3 actividades registradas

### Requirement: Monitor de seguimiento incluye métricas por alumno

El sistema SHALL incluir para cada alumno: cantidad de actividades totales, aprobadas, desaprobadas, pendientes, y porcentaje de avance.

#### Scenario: Métricas por alumno en seguimiento
- **WHEN** se consulta seguimiento
- **THEN** cada entrada de alumno incluye: nombre, email, comisión, regional, total actividades, aprobadas, desaprobadas, pendientes, porcentaje de aprobación
