## 1. Modelos

- [x] 1.1 Crear modelo `Calificacion` (id, tenant_id, entrada_padron_id, materia_id, actividad, nota_numerica nullable, nota_textual nullable, aprobado, origen enum Importado|Manual, importado_at — hereda SoftDeleteMixin)
- [x] 1.2 Crear modelo `UmbralMateria` (id, tenant_id, asignacion_id, materia_id, umbral_pct con default 60, valores_aprobatorios como ARRAY de texto — hereda SoftDeleteMixin)
- [x] 1.3 Registrar ambos modelos en `backend/app/models/__init__.py`

## 2. Migración

- [x] 2.1 Crear migration `0NN_create_calificacion_tables` con tablas `calificacion` y `umbral_materia`
- [x] 2.2 Índices: FK entrada_padron_id → entrada_padron.id; FK materia_id → materias.id; FK asignacion_id → asignaciones.id (nullable en UmbralMateria? No, es requerido); unique `(tenant_id, asignacion_id)` en umbral_materia; índice por `(tenant_id, materia_id, actividad)` en calificacion

## 3. Repositorios

- [x] 3.1 Crear `CalificacionRepository` (TenantScopedRepository[Calificacion]) con métodos:
  - [x] 3.1.1 `bulk_create_calificaciones(entries: list[dict])` — bulk insert con `session.add_all()` y flush
  - [x] 3.1.2 `list_by_materia(materia_id)` — lista calificaciones de una materia
  - [x] 3.1.3 `list_by_asignacion(materia_id, entrada_padron_ids: list)` — filtrar por asignación del docente
  - [x] 3.1.4 `find_sin_calificar(materia_id, entrada_padron_ids, actividades_textuales)` — cruce para reporte de finalización
  - [x] 3.1.5 `recalcular_aprobados(asignacion_id, umbral_pct, valores_aprobatorios)` — update masivo de `aprobado`
- [x] 3.2 Crear `UmbralMateriaRepository` (TenantScopedRepository[UmbralMateria]) con:
  - [x] 3.2.1 `get_by_asignacion(asignacion_id)` — obtiene el umbral de una asignación
  - [x] 3.2.2 `upsert(asignacion_id, materia_id, umbral_pct, valores_aprobatorios)` — crea o actualiza

## 4. Schemas (Pydantic v2, extra='forbid')

- [x] 4.1 Crear `ActividadDetectadaItem` (nombre, tipo: numerica|textual)
- [x] 4.2 Crear `CalificacionPreviewResponse` (actividades: list[ActividadDetectadaItem], alumnos_count: int, total_filas: int)
- [x] 4.3 Crear `CalificacionConfirmRequest` (materia_id, cohorte_id, actividades_seleccionadas: list[str], entries: list[dict])
- [x] 4.4 Crear `CalificacionConfirmResponse` (registros_creados: int, materia_id, cohorte_id)
- [x] 4.5 Crear `UmbralMateriaRequest` (asignacion_id, materia_id, umbral_pct: int, valores_aprobatorios: list[str])
- [x] 4.6 Crear `UmbralMateriaResponse` (id, asignacion_id, materia_id, umbral_pct, valores_aprobatorios)
- [x] 4.7 Crear `ReporteFinalizacionPreviewResponse` (actividades_textuales: list[str], entries: list[dict])
- [x] 4.8 Crear `EntradaSinCorregirItem` (alumno_nombre, actividad, fecha_finalizacion opcional)
- [x] 4.9 Crear `ReporteFinalizacionResponse` (sin_corregir: list[EntradaSinCorregirItem], total: int)

## 5. Servicios

- [x] 5.1 Crear `CalificacionService` con:
  - [x] 5.1.1 `preview_import(file)` — parsea xlsx/csv, detecta columnas numéricas (sufijo `(Real)`) y textuales, retorna actividades detectadas + cantidad de alumnos
  - [x] 5.1.2 `confirm_import(materia_id, cohorte_id, actividades_seleccionadas, entries, actor_id)` — para cada alumno × actividad seleccionada, crea `Calificacion` con `aprobado` derivado contra umbral vigente; genera audit `CALIFICACIONES_IMPORTAR`
  - [x] 5.1.3 `_derivar_aprobado(nota_numerica, nota_textual, umbral_pct, valores_aprobatorios)` — lógica pura de derivación (testeable sin DB)
  - [x] 5.1.4 `get_umbral(asignacion_id)` — retorna umbral configurado o default 60%
  - [x] 5.1.5 `configurar_umbral(asignacion_id, materia_id, umbral_pct, valores_aprobatorios, actor_id)` — crea/actualiza umbral, genera audit si cambia
  - [x] 5.1.6 `recalcular_aprobados(asignacion_id)` — recalcula `aprobado` para todas las calificaciones de la asignación
- [x] 5.2 Crear `ReporteFinalizacionService` con:
  - [x] 5.2.1 `procesar_reporte(file, materia_id)` — parsea archivo, identifica actividades textuales finalizadas sin calificación, retorna listado de posibles trabajos sin corregir

## 6. Routers

- [x] 6.1 Crear router `/api/v1/calificaciones` con:
  - [x] 6.1.1 `POST /preview` — subir archivo de calificaciones, retornar vista previa con actividades detectadas (permiso `calificaciones:importar`)
  - [x] 6.1.2 `POST /confirm` — confirmar importación con actividades seleccionadas (permiso `calificaciones:importar`)
  - [x] 6.1.3 `POST /reporte-finalizacion` — subir reporte de finalización, retornar listado de TPs sin corregir (permiso `calificaciones:importar`)
  - [x] 6.1.4 `GET /umbral` — obtener umbral de la asignación actual (permiso `calificaciones:importar`)
  - [x] 6.1.5 `PUT /umbral` — configurar/actualizar umbral (permiso `calificaciones:importar`)
  - [x] 6.1.6 `POST /umbral/recalcular` — disparar recálculo de aprobados (permiso `calificaciones:importar`)
- [x] 6.2 Registrar router en `backend/app/main.py`
- [x] 6.3 Registrar modelos en `backend/app/models/__init__.py` (ya cubierto en 1.3)

## 7. Tests

- [x] 7.1 Tests de derivación `aprobado`: 
  - [x] 7.1.1 Nota numérica >= umbral → true
  - [x] 7.1.2 Nota numérica < umbral → false
  - [x] 7.1.3 Solo nota textual aprobatoria → true
  - [x] 7.1.4 Solo nota textual no aprobatoria → false
- [x] 7.2 Tests de import: 
  - [x] 7.2.1 Preview con archivo xlsx válido detecta columnas numéricas y textuales
  - [x] 7.2.2 Preview con archivo csv válido
  - [x] 7.2.3 Preview con formato no soportado → 422
  - [x] 7.2.4 Preview sin columnas de actividad → lista vacía
  - [x] 7.2.5 Confirm import crea registros de Calificacion con aprobado derivado
  - [x] 7.2.6 Confirm import genera audit CALIFICACIONES_IMPORTAR
- [x] 7.3 Tests de selección de actividades:
  - [x] 7.3.1 Import solo incluye actividades seleccionadas
  - [x] 7.3.2 Actividades no seleccionadas no generan registros
- [x] 7.4 Tests de umbral por asignación:
  - [x] 7.4.1 Configurar umbral crea registro
  - [x] 7.4.2 Umbral del Docente A no afecta al Docente B
  - [x] 7.4.3 Sin umbral configurado usa default 60
  - [x] 7.4.4 Umbral fuera de rango 0-100 → 422
  - [x] 7.4.5 Recalcular aprobados tras cambio de umbral
- [x] 7.5 Tests de reporte de finalización:
  - [x] 7.5.1 Reporte detecta actividad textual finalizada sin calificación
  - [x] 7.5.2 Actividad numérica sin calificación no aparece en listado (RN-08)
  - [x] 7.5.3 Actividad con calificación existente no aparece
- [x] 7.6 Tests de tenant isolation:
  - [x] 7.6.1 Tenant A no ve calificaciones de Tenant B
  - [x] 7.6.2 Tenant A no ve umbrales de Tenant B
- [x] 7.7 Tests de permisos:
  - [x] 7.7.1 Sin `calificaciones:importar` → 403 en endpoints de calificaciones
