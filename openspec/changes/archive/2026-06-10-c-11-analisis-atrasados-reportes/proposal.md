## Why

El flujo central del PROFESOR (FL-02) requiere, una vez importadas las calificaciones y configurado el umbral (C-10), poder **analizar los resultados**: detectar alumnos atrasados, rankear por actividades aprobadas, generar reportes rápidos, calcular notas finales y exportar TPs sin corregir. Sin este change, los datos importados no tienen valor operativo — son solo números en la base. Además, COORDINADOR y ADMIN necesitan monitores transversales para supervisar el estado académico del tenant.

## What Changes

- Nuevo módulo `/api/analisis/*` con todas las rutas de análisis y reportes
- Nuevo **AnalisisService** con lógica de cómputo pura (funciones sin IO, testables sin DB)
- Nuevos repositories queries para soportar los cálculos (en `CalificacionRepository`)
- **8 endpoints** que cubren F2.2–F2.9:
  - `GET /api/analisis/atrasados` — alumnos atrasados por materia (F2.2)
  - `GET /api/analisis/ranking` — ranking de actividades aprobadas (F2.3)
  - `GET /api/analisis/reportes-rapidos` — métricas consolidadas por materia (F2.4)
  - `GET /api/analisis/notas-finales` — notas finales agrupadas por alumno (F2.5)
  - `GET /api/analisis/exportar-tps-sin-corregir` — descarga CSV (F2.6)
  - `GET /api/analisis/monitor-general` — monitor transversal coord/admin (F2.7)
  - `GET /api/analisis/monitor-seguimiento` — monitor tutor/profesor (F2.8)
  - `GET /api/analisis/monitor-seguimiento-extendido` — monitor coord/admin con fechas (F2.9)
- Nuevo permiso `atrasados:ver` (ya existe en seed de migración RBAC, solo verificar cobertura)
- Guard `require_permission("atrasados:ver")` en todos los endpoints
- Exportación en formato CSV (sin dependencias externas; alternativa XLSX discutible)
- Tests de unidad para la lógica de cómputo pura + tests de integración con DB real
- Migración: no se requieren nuevas tablas (solo lectura de `Calificacion`, `UmbralMateria`, `EntradaPadron`)

## Capabilities

### New Capabilities

- `atrasados-computo`: Cómputo de alumnos atrasados — cruza actividades por alumno contra umbral configurado, detecta faltantes y notas < umbral (F2.2, RN-06). Scope por materia. Filtros opcionales por alumno.
- `ranking-aprobadas`: Ranking descendente por cantidad de actividades aprobadas. Solo incluye alumnos con ≥1 aprobada (F2.3, RN-09).
- `reportes-rapidos`: Métricas clave consolidadas de una materia: total alumnos, total actividades, promedio general, aprobados vs desaprobados, distribución de notas (F2.4).
- `notas-finales`: Cálculo de nota final por alumno agrupando todas las actividades de la materia. Promedio simple de notas numéricas. Listo para exportar o registrar (F2.5).
- `exportar-tps-sin-corregir`: Archivo CSV descargable con el listado de entregas detectadas como pendientes de corrección (cruza reporte de finalización vs calificaciones, solo actividades textuales) (F2.6, RN-07/08).
- `monitor-general`: Vista transversal COORDINADOR/ADMIN de todos los alumnos del tenant con estado por actividad. Filtros: materia, regional, comisión, búsqueda libre, estado. Paginada (F2.7).
- `monitor-seguimiento`: Vista filtrable TUTOR/PROFESOR de alumnos asignados. Filtros: alumno, correo, comisión, regional, actividad, mínimo de actividad cumplida (F2.8).
- `monitor-seguimiento-extendido`: Extiende F2.8 para COORDINADOR/ADMIN agregando filtro por rango de fechas (F2.9).

### Modified Capabilities
- *(none — todas las capacidades son nuevas)*

## Impact

- **Backend**: nuevo `backend/app/services/analisis_service.py`, nuevos métodos query en `CalificacionRepository`, nuevo `backend/app/api/v1/routers/analisis.py`
- **Schemas**: nuevos Pydantic schemas en `backend/app/schemas/analisis.py` con `extra='forbid'`
- **Permisos**: verificar que `atrasados:ver` esté correctamente seedeado para PROFESOR (scope=propio), COORDINADOR (scope=global) y ADMIN (scope=global). TUTOR no tiene este permiso actualmente — evaluar si F2.2 requiere agregarlo.
- **Dependencias**: solo lectura de modelos existentes. Sin nuevas tablas. Sin nuevas dependencias Python (CSV nativo).
- **Tests**: `backend/tests/test_analisis_service.py` (lógica pura) + `backend/tests/test_analisis_api.py` (integración)
