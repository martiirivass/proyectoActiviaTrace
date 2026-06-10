## ADDED Requirements

### Requirement: Sistema calcula nota final agrupada por alumno

El sistema SHALL calcular una nota final por alumno para una materia, promediando todas las notas numéricas registradas. Las actividades exclusivamente textuales no se incluyen en el promedio.

#### Scenario: Nota final promedio de actividades numéricas
- **WHEN** el Alumno A tiene `nota_numerica = 80` en "TP1" y `nota_numerica = 90` en "TP2"
- **THEN** la nota final del Alumno A es 85.0

#### Scenario: Alumno sin notas numéricas no tiene nota final
- **WHEN** el Alumno B solo tiene actividades con `nota_textual` y sin `nota_numerica`
- **THEN** la nota final del Alumno B es null (sin valor)

#### Scenario: Alumno con mezcla de notas numéricas y textuales
- **WHEN** el Alumno C tiene `nota_numerica = 70` en "TP1" y solo `nota_textual` en "TP2"
- **THEN** la nota final del Alumno C es 70.0 (solo considera la numérica)

#### Scenario: Notas finales incluyen metadatos del alumno
- **WHEN** se consultan notas finales
- **THEN** cada entrada incluye: nombre completo, email, comisión, cantidad de actividades consideradas, nota final (o null), y listado de actividades individuales con su nota

### Requirement: Notas finales respetan filtro por materia

El sistema SHALL requerir `materia_id` como parámetro obligatorio.

#### Scenario: Notas finales filtradas por materia
- **WHEN** se consultan notas finales con `materia_id`
- **THEN** solo se retornan alumnos con calificaciones en esa materia
