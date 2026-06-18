## ADDED Requirements

### Requirement: Monitor general muestra estado transversal del tenant

El sistema SHALL proveer una vista consolidada de todos los alumnos del tenant con su estado de actividades por materia, accesible para COORDINADOR y ADMIN (F2.7).

#### Scenario: Monitor general retorna todos los alumnos con estado
- **WHEN** un COORDINADOR consulta el monitor general
- **THEN** el sistema retorna una lista paginada con cada alumno, su materia, cantidad de actividades totales, aprobadas, desaprobadas y pendientes

#### Scenario: Monitor general filtra por materia
- **WHEN** se consulta monitor general con `materia_id`
- **THEN** solo se retornan alumnos de esa materia

#### Scenario: Monitor general filtra por regional
- **WHEN** se consulta monitor general con `regional`
- **THEN** solo se retornan alumnos de esa regional

#### Scenario: Monitor general filtra por comisión
- **WHEN** se consulta monitor general con `comision`
- **THEN** solo se retornan alumnos de esa comisión

#### Scenario: Monitor general permite búsqueda libre por alumno
- **WHEN** se consulta monitor general con `busqueda = "Pérez"`
- **THEN** solo se retornan alumnos cuyo nombre o apellidos contienen "Pérez" (case-insensitive)

#### Scenario: Monitor general filtra por estado de actividad
- **WHEN** se consulta monitor general con `estado = "atrasado"`
- **THEN** solo se retornan alumnos clasificados como atrasados

#### Scenario: Monitor general soporta paginación
- **WHEN** se consulta monitor general con `page=2&page_size=50`
- **THEN** el sistema retorna la página solicitada con metadata de paginación (total, page, page_size, next_page, prev_page)

### Requirement: Monitor general permite exportar

El sistema SHALL permitir exportar los datos del monitor general como CSV.

#### Scenario: Exportar monitor general
- **WHEN** se solicita exportación del monitor general con los filtros actuales
- **THEN** el sistema retorna un archivo CSV con los datos completos (sin paginación)
