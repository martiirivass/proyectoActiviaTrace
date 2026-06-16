## ADDED Requirements

### Requirement: Tabla de notas finales con promedio por alumno

El sistema SHALL mostrar una tabla con las notas finales promedio de cada alumno en la comisión, calculadas a partir de las actividades numéricas.

#### Scenario: Notas finales cargan con datos de la comisión
- **WHEN** el usuario navega a la vista de notas finales
- **THEN** el sistema muestra una tabla con columnas: nombre completo, email, comisión, cantidad de actividades consideradas, nota final (o "—" si es null)

#### Scenario: Alumno sin notas numéricas muestra "—"
- **WHEN** un alumno solo tiene actividades textuales
- **THEN** la nota final muestra "—" (sin valor) con estilo atenuado

#### Scenario: Fila expandible muestra detalle de actividades
- **WHEN** el usuario hace clic en una fila de alumno
- **THEN** se expande una fila detalle con el listado de actividades individuales y su nota

#### Scenario: Carga muestra spinner
- **WHEN** las notas finales se están obteniendo
- **THEN** el sistema muestra un spinner

#### Scenario: Error de carga muestra alert
- **WHEN** la obtención de notas finales falla
- **THEN** el sistema muestra un alert de error con opción de reintentar
