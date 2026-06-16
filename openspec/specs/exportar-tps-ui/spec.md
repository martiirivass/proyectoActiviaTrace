# exportar-tps-ui Specification

## Purpose
TBD - created by archiving change c-22-frontend-academico-docente. Update Purpose after archive.
## Requirements
### Requirement: Botón de exportación descarga CSV de TPs sin corregir

El sistema SHALL proveer un botón de descarga que genere un archivo CSV con el listado de TPs sin corregir de la comisión.

#### Scenario: Botón de exportar presente en la vista
- **WHEN** el usuario navega a la vista de exportar TPs
- **THEN** el sistema muestra un botón "Exportar TPs sin corregir" con icono de descarga

#### Scenario: Descarga genera archivo CSV
- **WHEN** el usuario hace clic en exportar
- **THEN** el sistema descarga un archivo CSV con columnas: alumno, actividad, fecha_finalizacion (si disponible)

#### Scenario: Botón muestra spinner durante descarga
- **WHEN** el archivo se está generando y descargando
- **THEN** el botón muestra un spinner y se deshabilita

#### Scenario: Error en exportación muestra alert
- **WHEN** la generación del CSV falla
- **THEN** el sistema muestra un alert de error con opción de reintentar

#### Scenario: Vista sin datos muestra botón deshabilitado
- **WHEN** no hay TPs sin corregir en la comisión
- **THEN** el botón se muestra deshabilitado con tooltip "No hay TPs sin corregir"

