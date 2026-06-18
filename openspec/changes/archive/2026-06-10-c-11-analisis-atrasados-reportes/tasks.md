## 1. Pure Computation Functions (`analisis_calculos.py`)

- [x] 1.1 Create `backend/app/services/analisis_calculos.py` with typed dataclasses (`CalificacionData`, `UmbralData`, `AlumnoData`) for input/output of pure functions
- [x] 1.2 Implement `compute_atrasados()` — recibe lista de calificaciones + umbral + actividades esperadas, retorna alumnos atrasados con causa (actividad_faltante | nota_bajo_umbral) (RN-06)
- [x] 1.3 Implement `compute_ranking()` — agrupa por alumno, cuenta `aprobado=true`, filtra ≥1, ordena descendente (RN-09)
- [x] 1.4 Implement `compute_reporte_rapido()` — métricas consolidadas: total alumnos, total actividades, promedio general, aprobados/desaprobados por actividad
- [x] 1.5 Implement `compute_nota_final()` — promedio de notas numéricas por alumno, excluye textuales, soporta null si no hay numéricas
- [x] 1.6 Implement `compute_tps_sin_corregir()` — cruza reporte de finalización vs calificaciones, solo actividades textuales (RN-07/RN-08)
- [x] 1.7 Implement CSV builder (`build_csv_string()`) con escape anti-CSV-injection

## 2. Repository Methods (`CalificacionRepository`)

- [x] 2.1 Add `get_actividades_by_materia(materia_id) -> list[str]` — distinct actividades para una materia
- [x] 2.2 Add `get_calificaciones_with_alumno(materia_id) -> list[dict]` — join Calificacion + EntradaPadron trayendo nombre, apellidos, email, comision, regional
- [x] 2.3 Add `get_aggregated_by_materia(materia_id) -> dict` — count, avg, min, max de notas por materia
- [x] 2.4 Add `count_aprobados_desaprobados(materia_id) -> tuple[int, int]` — count donde aprobado=true/false
- [x] 2.5 Add `get_alumnos_en_padron(materia_id) -> list[EntradaPadron]` — alumnos del padrón para la materia (usado para detectar faltantes)

## 3. Service Layer (`AnalisisService`)

- [x] 3.1 Create `backend/app/services/analisis_service.py` with `AnalisisService(db, tenant_id)` que inyecta CalificacionRepository, UmbralMateriaRepository, EntradaPadronRepository
- [x] 3.2 Implement `get_atrasados(materia_id, busqueda=None)` — orquesta repo queries + `compute_atrasados()`, aplica scope propio/global según current_user
- [x] 3.3 Implement `get_ranking(materia_id)` — orquesta repo + `compute_ranking()`
- [x] 3.4 Implement `get_reportes_rapidos(materia_id)` — orquesta repo + `compute_reporte_rapido()`
- [x] 3.5 Implement `get_notas_finales(materia_id)` — orquesta repo + `compute_nota_final()`
- [x] 3.6 Implement `exportar_tps_sin_corregir(materia_id)` — cruza reporte de finalización (de ReporteFinalizacionRepository) + calificaciones, retorna CSV string
- [x] 3.7 Implement `get_monitor_general(filters)` — paginado, filtros: materia, regional, comision, busqueda, estado. Scope global
- [x] 3.8 Implement `get_monitor_seguimiento(user_id, filters)` — scope propio, filtros: alumno, email, comision, regional, actividad, min_actividades
- [x] 3.9 Implement `get_monitor_seguimiento_extendido(filters)` — como 3.8 pero scope global + filtros fecha_desde/fecha_hasta

## 4. Schemas Pydantic

- [x] 4.1 Create `backend/app/schemas/analisis.py` con todos los request/response schemas (extra='forbid'):
  - `AtrasadoItem`, `AtrasadosResponse`, `RankingItem`, `RankingResponse`
  - `ReporteRapidoResponse`, `NotaFinalItem`, `NotasFinalesResponse`
  - `MonitorGeneralItem`, `MonitorGeneralResponse`, `MonitorGeneralFilters`
  - `MonitorSeguimientoItem`, `MonitorSeguimientoResponse`, `MonitorSeguimientoFilters`

## 5. Router

- [x] 5.1 Create `backend/app/api/v1/routers/analisis.py` con prefijo `/api/v1/analisis` y tag "Análisis"
- [x] 5.2 Implement endpoint `GET /atrasados` — guard `atrasados:ver`, query params: materia_id (opcional), busqueda (opcional)
- [x] 5.3 Implement endpoint `GET /ranking` — guard `atrasados:ver`, query param: materia_id
- [x] 5.4 Implement endpoint `GET /reportes-rapidos` — guard `atrasados:ver`, query param: materia_id (requerido)
- [x] 5.5 Implement endpoint `GET /notas-finales` — guard `atrasados:ver`, query param: materia_id
- [x] 5.6 Implement endpoint `GET /exportar-tps-sin-corregir` — guard `atrasados:ver`, retorna StreamingResponse con CSV
- [x] 5.7 Implement endpoint `GET /monitor-general` — guard `atrasados:ver` + verificación scope global, filtros query params + paginación
- [x] 5.8 Implement endpoint `GET /monitor-seguimiento` — guard `atrasados:ver`, scope propio, filtros query params
- [x] 5.9 Implement endpoint `GET /monitor-seguimiento-extendido` — guard `atrasados:ver` + verificación scope global, filtros + fecha_desde/fecha_hasta
- [x] 5.10 Registrar router en `backend/app/api/v1/__init__.py` o `main.py`

## 6. Tests

- [x] 6.1 Unit tests para `compute_atrasados()`: 6 tests (bajo umbral, faltante, todas ok, textual, busqueda, sin califs) ✅
- [x] 6.2 Unit tests para `compute_ranking()`: 4 tests (descendente, excluye sin aprobadas, empate, porcentaje) ✅
- [x] 6.3 Unit tests para `compute_reporte_rapido()`: 3 tests (métricas, distribución, sin datos) ✅
- [x] 6.4 Unit tests para `compute_nota_final()`: 5 tests (promedio, solo textuales, mixto, múltiples, sin califs) ✅
- [x] 6.5 Unit tests para `compute_tps_sin_corregir()`: 3 tests + CSV builder 3 tests ✅
- [x] 6.6 Integration tests para `GET /api/v1/analisis/atrasados` con DB real ✅
- [x] 6.7 Integration tests para `GET /api/v1/analisis/ranking` con DB real ✅
- [x] 6.8 Integration tests para `GET /api/v1/analisis/exportar-tps-sin-corregir` con CSV response ✅
- [x] 6.9 Integration tests para monitores con filtros y paginación ✅
- [x] 6.10 Integration test: 403/401 cuando falta permiso `atrasados:ver` ✅

## 7. Migración y Permisos

- [x] 7.1 Verificado: `atrasados:ver` seedeado para PROFESOR (scope=propio), COORDINADOR (scope=global), ADMIN (scope=global) ✅
- [ ] 7.2 Pendiente: decidir si TUTOR necesita acceso a `atrasados:ver`
