# reportes-rapidos-vista Specification

## Purpose
TBD - created by archiving change c-22-frontend-academico-docente. Update Purpose after archive.
## Requirements
### Requirement: Reporte rápido muestra métricas consolidadas de la comisión

El sistema SHALL mostrar un reporte consolidado con métricas clave de la comisión seleccionada.

#### Scenario: Reporte carga métricas generales
- **WHEN** el usuario navega a la vista de reportes
- **THEN** el sistema muestra tarjetas con: total de alumnos, total de actividades, promedio general de notas numéricas, cantidad de aprobados, cantidad de desaprobados, porcentaje de aprobación general

#### Scenario: Distribución de aprobación por actividad
- **WHEN** el reporte carga
- **THEN** el sistema muestra una tabla con cada actividad: nombre, cantidad de alumnos con nota, promedio de la actividad, aprobados, desaprobados

#### Scenario: Gráfico de barras simple de distribución
- **WHEN** el reporte carga
- **THEN** el sistema muestra un gráfico de barras simple (CSS nativo o SVG sin librerías externas) con la distribución aprobados/desaprobados por actividad

#### Scenario: Reporte sin datos muestra estado informativo
- **WHEN** la comisión no tiene calificaciones importadas
- **THEN** el sistema muestra un mensaje "No hay datos disponibles para esta comisión"

#### Scenario: Carga muestra spinner
- **WHEN** el reporte se está obteniendo
- **THEN** el sistema muestra un spinner

#### Scenario: Error de carga muestra alert
- **WHEN** la obtención del reporte falla
- **THEN** el sistema muestra un alert de error con opción de reintentar

