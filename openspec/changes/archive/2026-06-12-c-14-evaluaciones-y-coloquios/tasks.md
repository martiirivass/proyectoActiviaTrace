## 1. Setup — Auditoría y Permisos

- [x] 1.1 Agregar códigos de auditoría `COLOQUIO_CREAR`, `COLOQUIO_EDITAR`, `COLOQUIO_CERRAR`, `RESERVA_CREAR`, `RESERVA_CANCELAR`, `RESULTADO_REGISTRAR` en `backend/app/core/audit_codes.py`
- [x] 1.2 Agregar permiso `coloquios:gestionar` en `backend/app/core/permissions.py`
- [x] 1.3 Agregar permiso `coloquios:reservar` en `backend/app/core/permissions.py`
- [x] 1.4 Asignar permiso `coloquios:gestionar` a roles PROFESOR, COORDINADOR y ADMIN en el seeder de RBAC
- [x] 1.5 Asignar permiso `coloquios:reservar` a rol ALUMNO en el seeder de RBAC

## 2. Modelos SQLAlchemy

- [x] 2.1 Crear `backend/app/models/evaluacion.py` con modelo `Evaluacion` (UUID PK, tenant_id, materia_id, cohorte_id, tipo: enum Parcial|TP|Coloquio|Recuperatorio, instancia: str, activa: bool default True, SoftDeleteMixin)
- [x] 2.2 Crear modelo `DiaConvocatoria` en el mismo archivo (UUID PK, tenant_id, evaluacion_id FK, fecha: Date, cupo_maximo: int, cupos_ocupados: int default 0, SoftDeleteMixin)
- [x] 2.3 Crear tabla puente `evaluacion_alumnos_convocados` (tabla asociativa entre Evaluacion y Usuario) con el modelo `EvaluacionAlumnoConvocado` (UUID PK, tenant_id, evaluacion_id FK, alumno_id FK, SoftDeleteMixin)
- [x] 2.4 Crear `backend/app/models/reserva_evaluacion.py` con modelo `ReservaEvaluacion` (UUID PK, tenant_id, evaluacion_id FK, dia_convocatoria_id FK, alumno_id FK, fecha_hora: DateTime, estado: enum Activa|Cancelada, SoftDeleteMixin)
- [x] 2.5 Crear `backend/app/models/resultado_evaluacion.py` con modelo `ResultadoEvaluacion` (UUID PK, tenant_id, evaluacion_id FK, alumno_id FK, nota_final: str, estado: enum Borrador|Definitivo, SoftDeleteMixin)
- [x] 2.6 Registrar los modelos y enums en `backend/app/models/__init__.py`

## 3. Migración Alembic

- [x] 3.1 Generar migración con `alembic revision --autogenerate -m "create_evaluacion_tables"`
- [x] 3.2 Revisar y ajustar la migración generada (verificar tipos, enums, FKs, índices)
- [x] 3.3 Ejecutar migración y verificar que las tablas se crean correctamente

## 4. Repositorios

- [x] 4.1 Crear `backend/app/repositories/evaluacion_repository.py` con `EvaluacionRepository` (hereda de `TenantScopedRepository[Evaluacion]`)
- [x] 4.2 Agregar métodos: `list_with_metrics()` con filtros (materia_id, cohorte_id, activa) que incluya total_convocados, reservas_activas, cupos_libres; `get_detail()` con días, convocados y métricas
- [x] 4.3 Agregar `DiaConvocatoriaRepository` con métodos: `get_by_id_with_lock()` (SELECT FOR UPDATE), `bulk_create()`, `get_by_evaluacion()`
- [x] 4.4 Agregar `EvaluacionAlumnoRepository` con métodos: `reemplazar_convocados()` (DELETE + INSERT en transacción), `list_by_evaluacion()`, `alumno_esta_convocado()`
- [x] 4.5 Crear `backend/app/repositories/reserva_repository.py` con `ReservaRepository` (hereda de `TenantScopedRepository[ReservaEvaluacion]`)
- [x] 4.6 Agregar métodos: `list_with_filters()` (evaluacion_id, materia_id, fecha_desde, fecha_hasta, estado, alumno_id), `get_activa_by_alumno_y_evaluacion()`, `get_agenda_admin()` con joins
- [x] 4.7 Crear `backend/app/repositories/resultado_repository.py` con `ResultadoRepository` (hereda de `TenantScopedRepository[ResultadoEvaluacion]`)
- [x] 4.8 Agregar métodos: `list_with_filters()`, `get_by_alumno_y_evaluacion()`, `get_metricas()` para el panel
- [x] 4.9 Registrar repositorios en `backend/app/repositories/__init__.py`

## 5. Schemas Pydantic

- [x] 5.1 Crear `backend/app/schemas/evaluaciones.py` con todos los schemas del módulo
- [x] 5.2 Schemas de convocatoria: `EvaluacionCreate` (materia_id, cohorte_id, tipo="Coloquio", instancia, dias: list[DiaConvocatoriaCreate]), `EvaluacionUpdate` (instancia), `EvaluacionResponse`, `EvaluacionDetailResponse` (con días, métricas, convocados), `EvaluacionListResponse` (paginado con métricas inline)
- [x] 5.3 Schemas de días: `DiaConvocatoriaCreate` (fecha, cupo_maximo), `DiaConvocatoriaResponse`
- [x] 5.4 Schemas de convocados: `ConvocadosUpdateRequest` (alumno_ids: list[uuid.UUID]), `AlumnoConvocadoResponse`
- [x] 5.5 Schemas de reserva: `ReservaCreate` (evaluacion_id, dia_convocatoria_id), `ReservaResponse`, `ReservaListResponse`, `ReservaAgendaResponse` (con datos de alumno y materia)
- [x] 5.6 Schemas de resultado: `ResultadoCreate` (evaluacion_id, alumno_id, nota_final), `ResultadoUpdate` (nota_final, estado), `ResultadoResponse`, `ResultadoListResponse`
- [x] 5.7 Schema `MetricasResponse` (total_alumnos_cargados, instancias_activas, reservas_activas, notas_registradas)
- [x] 5.8 Todos los response schemas con `ConfigDict(from_attributes=True, extra='forbid')`
- [x] 5.9 Registrar schemas en `backend/app/schemas/__init__.py`

## 6. Services

- [x] 6.1 Crear `backend/app/services/evaluacion_service.py` con `EvaluacionService`
- [x] 6.2 Implementar `crear_convocatoria()`: crear Evaluacion + bulk insert DiasConvocatoria en una transacción, auditar `COLOQUIO_CREAR`
- [x] 6.3 Implementar `editar_convocatoria()`: validar que no tenga reservas activas, auditar `COLOQUIO_EDITAR`
- [x] 6.4 Implementar `cerrar_convocatoria()`: setear activa=False, cancelar reservas activas, auditar `COLOQUIO_CERRAR`
- [x] 6.5 Implementar `importar_convocados()`: reemplazo atómico del padrón, validar que los UUIDs sean ALUMNO en el tenant
- [x] 6.6 Implementar `listar_convocatorias()`: delegar a repository con filtros y paginación
- [x] 6.7 Implementar `obtener_detalle()`: incluir días, métricas y convocados
- [x] 6.8 Crear `backend/app/services/reserva_service.py` con `ReservaService`
- [x] 6.9 Implementar `reservar_turno()`: validar alumno convocado, FOR UPDATE sobre DiaConvocatoria, verificar cupo, incrementar cupos_ocupados, crear ReservaEvaluacion, auditar `RESERVA_CREAR`
- [x] 6.10 Implementar `cancelar_reserva()`: validar ownership, cambiar estado, liberar cupo (decrementar cupos_ocupados), auditar `RESERVA_CANCELAR`
- [x] 6.11 Implementar `listar_agenda()`: con filtros y paginación para COORDINADOR/ADMIN
- [x] 6.12 Implementar `mis_reservas()`: listar reservas del alumno autenticado
- [x] 6.13 Crear `backend/app/services/resultado_service.py` con `ResultadoService`
- [x] 6.14 Implementar `registrar_resultado()`: validar no duplicado, crear en estado Borrador
- [x] 6.15 Implementar `actualizar_resultado()`: validar transición de estado Borrador→Definitivo, auditar `RESULTADO_REGISTRAR`
- [x] 6.16 Implementar `listar_resultados()`: con filtros y paginación
- [x] 6.17 Implementar `obtener_metricas()`: consultar las 4 métricas del tenant

## 7. Routers / API Endpoints

- [x] 7.1 Crear `backend/app/api/v1/routers/evaluaciones.py` con prefix `/api/v1/evaluaciones`
- [x] 7.2 Endpoint `POST /` — crear convocatoria, guard `coloquios:gestionar`
- [x] 7.3 Endpoint `GET /` — listar convocatorias, guard `coloquios:gestionar`
- [x] 7.4 Endpoint `GET /{id}` — detalle de convocatoria, guard `coloquios:gestionar`
- [x] 7.5 Endpoint `PATCH /{id}` — editar convocatoria, guard `coloquios:gestionar`
- [x] 7.6 Endpoint `POST /{id}/cerrar` — cerrar convocatoria, guard `coloquios:gestionar` + verificar rol ADMIN
- [x] 7.7 Endpoint `POST /{id}/convocados` — importar padrón, guard `coloquios:gestionar`
- [x] 7.8 Endpoint `GET /{id}/convocados` — listar convocados, guard `coloquios:gestionar`
- [x] 7.9 Endpoint `POST /reservas` — reservar turno, guard `coloquios:reservar`
- [x] 7.10 Endpoint `POST /reservas/{id}/cancelar` — cancelar reserva, guard `coloquios:reservar`
- [x] 7.11 Endpoint `GET /reservas` — agenda consolidada, guard `coloquios:gestionar`
- [x] 7.12 Endpoint `GET /reservas/mis-reservas` — reservas del alumno, guard `coloquios:reservar`
- [x] 7.13 Endpoint `POST /resultados` — registrar resultado, guard `coloquios:gestionar`
- [x] 7.14 Endpoint `PATCH /resultados/{id}` — actualizar resultado, guard `coloquios:gestionar`
- [x] 7.15 Endpoint `GET /resultados` — listar resultados, guard `coloquios:gestionar`
- [x] 7.16 Endpoint `GET /metricas` — panel de métricas, guard `coloquios:gestionar`
- [x] 7.17 Registrar router en `backend/app/main.py`

## 8. Tests

- [x] 8.1 Crear `backend/tests/test_evaluaciones.py` con fixtures de setup (tenant, usuario COORDINADOR, alumno, materia, cohorte)
- [x] 8.2 Test: crear convocatoria con 3 días y verificar persistencia
- [x] 8.3 Test: crear convocatoria sin días → 422
- [x] 8.4 Test: importar padrón de convocados → verificar reemplazo atómico
- [x] 8.5 Test: importar padrón con UUID inválido → 422
- [x] 8.6 Test: listar convocatorias con métricas
- [x] 8.7 Test: editar convocatoria
- [x] 8.8 Test: editar convocatoria con reservas activas → 409
- [x] 8.9 Test: cerrar convocatoria → verificar cancelación de reservas
- [x] 8.10 Test: reservar turno con cupo disponible → verificar decremento
- [x] 8.11 Test: reservar turno sin cupo → 409
- [x] 8.12 Test: reservar duplicada → 409
- [x] 8.13 Test: alumno no convocado intenta reservar → 403
- [x] 8.14 Test: cancelar reserva → verificar liberación de cupo
- [x] 8.15 Test: cancelar reserva ajena → 403
- [x] 8.16 Test: agenda consolidada con filtros
- [x] 8.17 Test: alumno consulta mis-reservas
- [x] 8.18 Test: registrar resultado → verificar creación
- [x] 8.19 Test: resultado duplicado → 409
- [x] 8.20 Test: actualizar resultado Borrador → Definitivo
- [x] 8.21 Test: rechazar cambio Definitivo → Borrador
- [x] 8.22 Test: panel de métricas
- [x] 8.23 Test: ALUMNO no puede acceder a métricas → 403
- [x] 8.24 Test: aislamiento tenant — datos del tenant A no visibles en tenant B
- [x] 8.25 Test: concurrencia — dos reservas simultáneas no sobrepasan cupo
