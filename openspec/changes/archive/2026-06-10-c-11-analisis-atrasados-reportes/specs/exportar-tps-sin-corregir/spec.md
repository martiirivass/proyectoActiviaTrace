## ADDED Requirements

### Requirement: Sistema exporta TPs sin corregir como CSV

El sistema SHALL generar un archivo CSV descargable con el listado de entregas finalizadas por el alumno pero sin calificación registrada, cruzando el reporte de finalización del LMS con las calificaciones importadas (RN-07).

#### Scenario: Exportar TPs sin corregir genera CSV
- **WHEN** se solicita exportación para una materia con datos de reporte de finalización y calificaciones
- **THEN** el sistema retorna un archivo CSV con columnas: alumno, actividad, fecha_finalizacion (si disponible)

#### Scenario: CSV incluye header Content-Type y Content-Disposition
- **WHEN** se descarga el CSV
- **THEN** la respuesta incluye `Content-Type: text/csv` y `Content-Disposition: attachment; filename="tps_sin_corregir_<materia>.csv"`

#### Scenario: CSV escapa valores peligrosos para Excel
- **WHEN** un valor en el CSV comienza con `=`, `+`, `-` o `@`
- **THEN** el sistema antepone `\t` para prevenir CSV injection

### Requirement: Exportación solo incluye actividades textuales (RN-08)

El sistema SHALL incluir únicamente actividades de escala textual en el reporte de TPs sin corregir (RN-08). Las actividades numéricas se excluyen porque ausencia de nota equivale a no entregado.

#### Scenario: Actividad numérica sin calificación no se incluye
- **WHEN** una actividad numérica "TP1 (Real)" no tiene calificación para un alumno
- **THEN** esa combinación NO aparece en el CSV de TPs sin corregir

#### Scenario: Actividad textual finalizada sin calificación sí se incluye
- **WHEN** una actividad textual "Estado TP1" está marcada como finalizada en el reporte pero no tiene calificación
- **THEN** esa combinación SÍ aparece en el CSV

### Requirement: Exportación requiere materia_id

El sistema SHALL requerir `materia_id` como parámetro.

#### Scenario: Exportación sin materia_id es rechazada
- **WHEN** se solicita exportación sin `materia_id`
- **THEN** el sistema rechaza con error 422
