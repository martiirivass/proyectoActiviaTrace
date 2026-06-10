## Why

El flujo central del PROFESOR (FL-02) requiere importar calificaciones del LMS y configurar el umbral de aprobación como paso previo al análisis de atrasados (C-11) y comunicaciones (C-12). Sin modelos de `Calificacion` y `UmbralMateria`, el sistema no puede computar aprobados, detectar entregas sin corregir ni rankear alumnos. Es el próximo change en el camino crítico después de `C-09 padron-ingesta-moodle`.

## What Changes

- Crear modelo `Calificacion` (numérica/textual, `aprobado` derivado, origen Importado/Manual)
- Crear modelo `UmbralMateria` (umbral_pct por asignación, valores aprobatorios textuales)
- Importar calificaciones desde archivo del LMS (F1.1): detecta columnas numéricas (RN-01: encabezado termina en `(Real)`) y textuales (RN-02), vista previa de actividades detectadas, selección por el usuario
- Importar reporte de finalización (F1.2): detecta TPs entregados sin nota (RN-07, RN-08)
- Configurar umbral por materia (F2.1, RN-03, defecto 60%)
- Log de auditoría `CALIFICACIONES_IMPORTAR` en toda importación (código ya existe en `audit_codes.py`)
- Endpoints REST para importar, previsualizar, seleccionar actividades, configurar umbral
- Migración Alembic: tablas `calificacion` y `umbral_materia`

## Capabilities

### New Capabilities
- `calificaciones-importar`: Importación de calificaciones desde archivo xlsx/csv del LMS con detección automática de columnas numéricas (RN-01) y textuales (RN-02), vista previa de actividades detectadas, selección de actividades a incluir, confirmación de importación con persistencia y auditoría.
- `reporte-finalizacion`: Importación de reporte de finalización de actividades del LMS para detectar entregas finalizadas por el alumno pero sin calificación registrada (RN-07, RN-08). Genera listado de posibles trabajos sin corregir.
- `umbral-materia`: Configuración del porcentaje mínimo de aprobación (umbral_pct) y valores textuales aprobatorios por asignación docente + materia. Defecto 60% (RN-03). El umbral es por asignación (no afecta a otros docentes). Si no existe configuración, se usa el valor por defecto del tenant.

### Modified Capabilities
- *(ninguna — son capabilities nuevas)*

## Impact

- **Nuevos modelos**: `Calificacion`, `UmbralMateria` en `backend/app/models/`
- **Nuevo repositorio**: `CalificacionRepository` scoped por tenant (tenant_id en todos los queries)
- **Nuevo servicio**: `CalificacionService` con lógica de:
  - Parseo de archivo LMS (detección columnas `(Real)`, valores textuales)
  - Derivación de `aprobado` (numérica vs umbral, textual vs conjunto aprobatorio)
  - Detección de entregas sin corregir (cruce con reporte de finalización)
  - Configuración de umbral por asignación
- **Nuevos schemas**: Pydantic v2 con `extra='forbid'` para preview, confirmación de import, selección de actividades, umbral config
- **Nuevos routers**: `/api/v1/calificaciones/*` con permiso `calificaciones:importar`
- **Migración**: Alembic `0NN_create_calificacion_tables` (Calificacion, UmbralMateria)
- **Audit**: código `CALIFICACIONES_IMPORTAR` ya existe en `audit_codes.py` — se reusa
- **Tests**: derivación `aprobado` (numérica vs umbral, textual vs conjunto), import + preview con detección de columnas, selección de actividades, umbral por asignación (no afecta otros docentes), auditoría
