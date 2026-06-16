## ADDED Requirements

### Requirement: Monitor de seguimiento con filtros y métricas por alumno

El sistema SHALL mostrar una vista de seguimiento para TUTOR/PROFESOR con tabla filtrable de alumnos y sus métricas de actividad.

#### Scenario: Monitor carga alumnos del usuario
- **WHEN** un TUTOR o PROFESOR navega a `/monitor`
- **THEN** el sistema muestra una tabla con los alumnos bajo su asignación, cada fila con: nombre, email, comisión, regional, total actividades, aprobadas, desaprobadas, pendientes, porcentaje de aprobación

#### Scenario: Filtro por nombre de alumno
- **WHEN** el usuario escribe en el campo de búsqueda por alumno
- **THEN** la tabla se filtra por nombre del alumno

#### Scenario: Filtro por email
- **WHEN** el usuario ingresa un email en el filtro
- **THEN** la tabla se filtra por email del alumno

#### Scenario: Filtro por comisión
- **WHEN** el usuario selecciona una comisión en el filtro
- **THEN** la tabla se filtra a los alumnos de esa comisión

#### Scenario: Filtro por regional
- **WHEN** el usuario selecciona una regional en el filtro
- **THEN** la tabla se filtra a los alumnos de esa regional

#### Scenario: Filtro por actividad específica
- **WHEN** el usuario ingresa un nombre de actividad
- **THEN** la tabla se filtra mostrando solo el estado de esa actividad

#### Scenario: Filtro por mínimo de actividades
- **WHEN** el usuario ingresa un número en "min_actividades"
- **THEN** la tabla solo muestra alumnos con al menos esa cantidad de actividades registradas

#### Scenario: Filtros actúan en combinación (AND)
- **WHEN** el usuario aplica múltiples filtros simultáneamente
- **THEN** la tabla muestra solo los alumnos que cumplen TODOS los filtros

#### Scenario: Porcentaje de aprobación con barra de progreso
- **WHEN** el monitor muestra el porcentaje
- **THEN** se renderiza una barra de progreso visual con color según rango (verde >70%, amarillo 40-70%, rojo <40%)

#### Scenario: Carga muestra spinner
- **WHEN** los datos del monitor se están obteniendo
- **THEN** el sistema muestra un spinner

#### Scenario: Error de carga muestra alert
- **WHEN** la obtención del monitor falla
- **THEN** el sistema muestra un alert de error con opción de reintentar

#### Scenario: Sin alumnos muestra estado vacío
- **WHEN** el usuario no tiene alumnos asignados
- **THEN** el sistema muestra "No hay alumnos asignados para seguimiento"
