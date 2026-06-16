# calificaciones-import-ui Specification

## Purpose
TBD - created by archiving change c-22-frontend-academico-docente. Update Purpose after archive.
## Requirements
### Requirement: Wizard de importación guía al usuario en 3 pasos

El sistema SHALL proveer un flujo wizard de 3 pasos para importar calificaciones: Upload → Preview → Confirm.

#### Scenario: Paso 1 — Upload muestra dropzone para archivo
- **WHEN** el usuario accede a la vista de importación
- **THEN** el sistema muestra un área de dropzone que acepta archivos `.xlsx` y `.csv`, con botón alternativo de selección

#### Scenario: Paso 1 — Upload rechaza formato no soportado
- **WHEN** el usuario selecciona un archivo que no es `.xlsx` ni `.csv`
- **THEN** el sistema muestra error "Formato no soportado. Use archivos .xlsx o .csv" y no habilita el botón de continuar

#### Scenario: Paso 2 — Preview muestra tabla de alumnos × actividades
- **WHEN** el usuario sube un archivo válido y recibe el preview del servidor
- **THEN** el sistema muestra una tabla donde las filas son alumnos y las columnas son actividades detectadas, con los valores parseados

#### Scenario: Paso 2 — Preview permite seleccionar actividades
- **WHEN** el usuario está en el paso de preview
- **THEN** cada columna de actividad tiene un checkbox para incluirla/excluirla de la importación, con todas seleccionadas por defecto

#### Scenario: Paso 2 — Preview muestra metadatos del alumno
- **WHEN** el archivo contiene columnas de metadatos (apellido, nombre, email)
- **THEN** el sistema las muestra como columnas fijas en la tabla (no seleccionables)

#### Scenario: Paso 2 — Preview sin actividades detectables
- **WHEN** el archivo no tiene columnas reconocidas como actividades
- **THEN** el sistema muestra mensaje "No se detectaron actividades en el archivo" y disabled el botón de continuar

#### Scenario: Paso 3 — Confirm muestra resumen antes de importar
- **WHEN** el usuario avanza al paso de confirmación
- **THEN** el sistema muestra un resumen: materia, cohorte, cantidad de actividades a importar, cantidad de alumnos afectados, y botón "Confirmar importación"

#### Scenario: Paso 3 — Confirmación exitosa muestra resultado
- **WHEN** la importación se completa exitosamente
- **THEN** el sistema muestra un alert de éxito con la cantidad de registros creados y un botón "Volver a calificaciones"

#### Scenario: Paso 3 — Error en importación muestra mensaje
- **WHEN** la importación falla
- **THEN** el sistema muestra un alert de error con el mensaje del servidor y opción de reintentar

#### Scenario: Wizard permite navegar paso atrás
- **WHEN** el usuario está en paso 2 o 3
- **THEN** hay un botón "Atrás" que vuelve al paso anterior conservando los datos ya cargados

#### Scenario: Indicador de progreso del wizard
- **WHEN** el wizard está activo
- **THEN** se muestra un indicador visual de progreso (paso 1/3, 2/3, 3/3) con el paso actual resaltado

### Requirement: Importación muestra estado de carga durante subida y confirmación

El sistema SHALL mostrar indicadores de carga durante operaciones asíncronas (subida de archivo, confirmación de importación).

#### Scenario: Botón de subida muestra spinner durante upload
- **WHEN** el archivo se está subiendo al servidor para preview
- **THEN** el botón de subir muestra un spinner y se deshabilita

#### Scenario: Botón de confirmar muestra spinner durante importación
- **WHEN** la importación se está procesando
- **THEN** el botón "Confirmar importación" muestra un spinner y se deshabilita

