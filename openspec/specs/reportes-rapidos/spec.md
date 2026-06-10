## ADDED Requirements

### Requirement: Sistema genera reporte rápido con métricas consolidadas por materia

El sistema SHALL generar un reporte consolidado con métricas clave de una materia a partir de las calificaciones importadas.

#### Scenario: Reporte incluye métricas de alumnos y actividades
- **WHEN** se consulta reporte rápido para una materia con datos importados
- **THEN** el reporte incluye: total de alumnos, total de actividades, promedio general de notas numéricas, cantidad de aprobados, cantidad de desaprobados, y porcentaje de aprobación general

#### Scenario: Reporte incluye distribución de aprobación por actividad
- **WHEN** se consulta reporte rápido
- **THEN** cada actividad listada incluye: nombre de la actividad, cantidad de alumnos con nota, promedio de la actividad, cantidad de aprobados, cantidad de desaprobados

#### Scenario: Reporte para materia sin datos retorna estado informativo
- **WHEN** se consulta reporte rápido para una materia sin calificaciones importadas
- **THEN** el sistema retorna un estado informativo indicando que no hay datos disponibles

### Requirement: Reporte rápido respeta filtro por materia

El sistema SHALL requerir `materia_id` como parámetro obligatorio.

#### Scenario: Reporte sin materia_id es rechazado
- **WHEN** se consulta reporte rápido sin especificar `materia_id`
- **THEN** el sistema rechaza con error 422 indicando que materia_id es requerido
