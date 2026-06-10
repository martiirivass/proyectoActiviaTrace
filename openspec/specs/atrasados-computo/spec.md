## ADDED Requirements

### Requirement: Sistema computa alumnos atrasados por materia (RN-06)

El sistema SHALL computar la lista de alumnos atrasados para una materia según RN-06: un alumno está atrasado si tiene actividades faltantes (sin registro de calificación) o si su nota registrada es inferior al umbral configurado.

#### Scenario: Alumno con nota inferior al umbral es marcado como atrasado
- **WHEN** se consultan atrasados para una materia donde el Alumno A tiene `nota_numerica = 40` en "TP1" y el umbral configurado es 60
- **THEN** el Alumno A aparece en la lista de atrasados con la actividad "TP1" como causa "nota_bajo_umbral"

#### Scenario: Alumno con actividad faltante es marcado como atrasado
- **WHEN** se consultan atrasados para una materia con actividades esperadas ["TP1", "TP2", "TP3"] y el Alumno B tiene calificación solo en "TP1" y "TP2"
- **THEN** el Alumno B aparece en la lista de atrasados con la actividad "TP3" como causa "actividad_faltante"

#### Scenario: Alumno con todas las actividades aprobadas no aparece como atrasado
- **WHEN** se consultan atrasados para una materia donde el Alumno C tiene todas las actividades con `aprobado = true`
- **THEN** el Alumno C NO aparece en la lista de atrasados

#### Scenario: Alumno con nota textual aprobatoria no es atrasado
- **WHEN** el Alumno D tiene `nota_textual = "Satisfactorio"` y `aprobado = true` en todas las actividades
- **THEN** el Alumno D NO aparece en la lista de atrasados

#### Scenario: Filtro opcional por búsqueda de alumno
- **WHEN** se consultan atrasados con `busqueda = "García"` para una materia
- **THEN** solo se retornan alumnos atrasados cuyo nombre o apellidos contienen "García"

#### Scenario: Endpoint requiere permiso atrasados:ver
- **WHEN** un usuario sin permiso `atrasados:ver` intenta acceder al endpoint
- **THEN** el sistema rechaza con 403 Forbidden

### Requirement: Scope propio limita datos según el rol

El sistema SHALL limitar los datos visibles según el scope del permiso `atrasados:ver`: scope `propio` (PROFESOR, TUTOR) solo ve alumnos de sus asignaciones; scope `global` (COORDINADOR, ADMIN) ve todos los alumnos del tenant.

#### Scenario: PROFESOR solo ve alumnos de sus materias
- **WHEN** un PROFESOR con scope `propio` consulta atrasados sin especificar materia
- **THEN** el sistema solo retorna atrasados de las materias donde el PROFESOR tiene asignación activa

#### Scenario: COORDINADOR ve alumnos de cualquier materia
- **WHEN** un COORDINADOR con scope `global` consulta atrasados
- **THEN** el sistema retorna atrasados de todas las materias del tenant (sujeto a filtros)
