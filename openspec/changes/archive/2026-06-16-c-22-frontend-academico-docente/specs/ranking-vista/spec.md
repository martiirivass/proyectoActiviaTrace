## ADDED Requirements

### Requirement: Ranking muestra tabla ordenable de actividades aprobadas

El sistema SHALL mostrar una tabla descendente por cantidad de actividades aprobadas por alumno en la comisión.

#### Scenario: Ranking carga con datos de la comisión
- **WHEN** el usuario navega a la vista de ranking
- **THEN** el sistema muestra una tabla ordenable con columnas: posición, nombre completo, email, comisión, cantidad de aprobadas, total de actividades, porcentaje de aprobación

#### Scenario: Ranking ordenado por aprobadas descendente
- **WHEN** el ranking carga
- **THEN** los alumnos aparecen ordenados de mayor a menor cantidad de actividades aprobadas

#### Scenario: Alumno sin aprobadas no aparece
- **WHEN** un alumno tiene 0 actividades aprobadas
- **THEN** no aparece en el ranking

#### Scenario: Empate se ordena alfabéticamente
- **WHEN** dos alumnos tienen la misma cantidad de aprobadas
- **THEN** aparecen ordenados alfabéticamente por apellido y nombre

#### Scenario: Porcentaje se muestra con barra de progreso
- **WHEN** el ranking muestra el porcentaje
- **THEN** se renderiza una barra de progreso visual además del valor numérico

#### Scenario: Carga muestra spinner
- **WHEN** el ranking se está obteniendo
- **THEN** el sistema muestra un spinner

#### Scenario: Error de carga muestra alert
- **WHEN** la obtención del ranking falla
- **THEN** el sistema muestra un alert de error con opción de reintentar
