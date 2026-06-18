# atrasados-vista Specification

## Purpose
TBD - created by archiving change c-22-frontend-academico-docente. Update Purpose after archive.
## Requirements
### Requirement: Tabla de atrasados muestra alumnos con filtro de búsqueda

El sistema SHALL mostrar una tabla paginada con los alumnos atrasados de la comisión, con filtro por búsqueda textual.

#### Scenario: Tabla carga atrasados de la comisión
- **WHEN** el usuario navega a la vista de atrasados
- **THEN** el sistema muestra una tabla con columnas: alumno, email, actividad, causa (nota_bajo_umbral / actividad_faltante)

#### Scenario: Causa se muestra con badge de color
- **WHEN** la tabla muestra la causa del atraso
- **THEN** "nota_bajo_umbral" se muestra como badge rojo y "actividad_faltante" como badge naranja

#### Scenario: Filtro por búsqueda de alumno
- **WHEN** el usuario escribe en el campo de búsqueda
- **THEN** la tabla se filtra en tiempo real (debounced) por nombre o apellido del alumno, consumiendo el endpoint con `busqueda` param

#### Scenario: Tabla vacía muestra mensaje sin atrasados
- **WHEN** no hay alumnos atrasados en la comisión
- **THEN** el sistema muestra un estado vacío con mensaje "No hay alumnos atrasados en esta comisión"

#### Scenario: Carga de atrasados muestra spinner
- **WHEN** la lista se está obteniendo
- **THEN** el sistema muestra un spinner

#### Scenario: Error de carga muestra alert
- **WHEN** la obtención de atrasados falla
- **THEN** el sistema muestra un alert de error con opción de reintentar

#### Scenario: Botón para comunicarse con alumno atrasado
- **WHEN** el usuario pasa el mouse sobre una fila de atrasado
- **THEN** aparece un botón "Comunicar" que navega a la pestaña de comunicaciones con ese alumno preseleccionado como destinatario

### Requirement: Vista incluye resumen de atrasados

El sistema SHALL mostrar un resumen numérico de la situación de atraso en la comisión.

#### Scenario: Resumen muestra total de atrasados
- **WHEN** la tabla de atrasados carga
- **THEN** el sistema muestra en la parte superior un resumen: "X alumnos atrasados de Y totales"

