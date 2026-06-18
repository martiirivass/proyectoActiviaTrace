## Context

El módulo de **Evaluaciones y Coloquios** cubre la Épica 7 del producto. Los PROFESORES necesitan convocar alumnos a instancias de evaluación oral (coloquio), definir días disponibles con cupos, y gestionar la reserva de turnos. Los COORDINADORES necesitan visibilidad transversal de agendas y registro académico consolidado. Los ALUMNOS necesitan reservar y cancelar turnos.

Actualmente el backend tiene una arquitectura consolidada:
- FastAPI con routers → services → repositories (TenantScopedRepository)
- SQLAlchemy 2.0 async con modelos que heredan de `SoftDeleteMixin` y usan UUID PK
- Pydantic v2 schemas con `ConfigDict(extra='forbid')`
- Permisos finos via `require_permission(codename)`
- Auditoría via `AuditService.log(...)` con códigos en `audit_codes.py`
- Tests con base de datos real (sin mocks de DB)

Este change sigue el patrón establecido. Governance level: MEDIO — implementación con checkpoints.

## Goals / Non-Goals

**Goals:**
- Modelar `Evaluacion`, `ReservaEvaluacion` y `ResultadoEvaluacion` con soft delete y tenant scope
- Implementar importación de padrón de alumnos habilitados por convocatoria
- Implementar creación/edición/cierre de convocatorias con días y cupos
- Implementar listado de convocatorias con métricas (convocados, reservas, cupos)
- Implementar reserva y cancelación de turnos por alumno con control de cupo
- Implementar agenda consolidada de reservas con filtros para COORDINADOR/ADMIN
- Implementar registro académico consolidado con notas finales
- Implementar panel de métricas del módulo
- Proteger el módulo con permisos `coloquios:gestionar` y `coloquios:reservar`
- Auditoría de todas las operaciones del módulo

**Non-Goals:**
- Integración con LMS para reserva externa (PA-14: se asume reserva dentro del sistema)
- Notificaciones automáticas al crear/modificar convocatorias
- Tipos de evaluación distintos a coloquio (Parcial, TP, Recuperatorio) — el modelo lo soporta pero el módulo se enfoca en coloquios
- Frontend de este módulo (se implementa en C-23/C-24)
- Eliminación física de datos (soft delete solamente)
- Cupos por franja horaria (solo cupo global por día)

## Decisions

### D1: Importación de padrón como endpoint separado (no upsert destructivo)
- **Opción A (elegida)**: `POST /api/v1/evaluaciones/{id}/convocados` recibe lista de UUIDs de alumnos. Agrega al padrón sin reemplazar. El endpoint repone el padrón completo (reemplazo atómico).
- **Opción B**: Importación tipo upsert destructivo como F1.3.
- **Razón**: El padrón de coloquio es una lista de habilitados, no un reemplazo de datos. Cada convocatoria tiene su propio padrón independiente. Se opta por reemplazo completo (similar a F1.3) para simplicidad: quien importa sube el listado completo de habilitados y el sistema reemplaza. La relación se modela como tabla puente `evaluacion_alumno` entre Evaluacion y Usuario.

### D2: Cupo como columna en la tabla de días disponibles (dias_convocatoria)
- **Opción A (elegida)**: Tabla separada `DiaConvocatoria` con columnas `fecha`, `cupo_maximo`, `cupos_ocupados`. El service verifica y actualiza el cupo en una transacción.
- **Opción B**: Cupo como JSON array en la Evaluacion.
- **Razón**: Modelo relacional limpio que permite consultas eficientes ("días con cupo disponible"), control de concurrencia con `FOR UPDATE`, y escalabilidad a franjas horarias en el futuro.

### D3: Control de concurrencia con SELECT FOR UPDATE + verificación en service
- **Opción A (elegida)**: Al reservar, el service inicia transacción, hace `SELECT ... FOR UPDATE` sobre el `DiaConvocatoria` para bloquear la fila, verifica `cupos_ocupados < cupo_maximo`, incrementa, crea `ReservaEvaluacion`, commitea.
- **Opción B**: Optimistic locking con version column.
- **Razón**: El cupo es un recurso compartido crítico. `FOR UPDATE` es el mecanismo más robusto en PostgreSQL para garantizar que dos requests simultáneos no sobrepasen el cupo. Optimistic locking requeriría reintentos del lado del cliente y no es idiomático en APIs REST.

### D4: Días disponibles inline en la creación de convocatoria
- **Opción A (elegida)**: El schema `EvaluacionCreate` incluye un array `dias: list[DiaConvocatoriaCreate]` con fecha, cupo_maximo. El service crea en una sola operación la Evaluacion + N DiasConvocatoria.
- **Opción B**: Endpoint separado para agregar días a una convocatoria existente.
- **Razón**: La creación de convocatoria y sus días es una operación atómica del dominio. Separarlo crearía estados inconsistentes (convocatoria sin días). Si se necesita editar días después, se hará via endpoint PATCH específico.

### D5: ResultadoEvaluacion actualizable (no inmutable)
- **Opción A (elegida)**: El resultado se crea con `nota_final` y se puede actualizar (PATCH). Sin soft delete — se usa exclusión lógica via estado borrador/definitivo.
- **Opción B**: Resultado inmutable, solo append versiones.
- **Razón**: El PROFESOR/COORDINADOR puede corregir la nota. Un campo `estado: Borrador | Definitivo` permite controlar cuándo está firme. El audit log registra cada cambio.

### D6: Endpoints planos bajo /api/v1/evaluaciones (no sub-routers anidados)
- **Opción A (elegida)**: Un solo router `evaluaciones.py` con prefijo `/api/v1/evaluaciones`. Las rutas de reservas y resultados usan sub-prefijos: `/api/v1/evaluaciones/reservas`, `/api/v1/evaluaciones/resultados`.
- **Opción B**: Routers separados para cada recurso.
- **Razón**: Un solo router mantiene cohesión del módulo. Es el patrón usado en C-13 (encuentros + guardias comparten un router cada uno). Si el módulo crece mucho, se puede dividir.

### D7: Permiso `coloquios:gestionar` para PROFESOR/COORDINADOR/ADMIN y `coloquios:reservar` para ALUMNO
- **Opción A (elegida)**: Dos permisos diferenciados. `coloquios:gestionar` cubre CRUD de convocatorias, importación de padrón, registro de notas. `coloquios:reservar` cubre reserva y cancelación de turnos.
- **Opción B**: Un solo permiso `coloquios:gestionar` para todo.
- **Razón**: El ALUMNO no debe tener acceso a gestión de convocatorias. Separar permisos por actor es consistente con el modelo RBAC fino del sistema.

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|-----------|
| [R1] Control de concurrencia con `FOR UPDATE` puede generar deadlocks si dos transacciones intentan reservar el mismo día simultáneamente | Usar `ORDER BY` en el SELECT para garantizar orden consistente de locks. Timeout de transacción corto (5s). El error se propaga al cliente como 409 Conflict. |
| [R2] Importación de padrón con reemplazo atómico puede ser lenta para listas grandes (>1000 alumnos) | Usar operación bulk: DELETE + INSERT en una sola transacción. Para listas muy grandes (>5000), considerar chunked insert. |
| [R3] Cupo por día sin franja horaria puede ser insuficiente si un día tiene múltiples horarios | El modelo `DiaConvocatoria` está preparado para agregar `hora_desde` y `hora_hasta` en el futuro sin cambiar la estructura de cupo. |
| [R4] PA-14 no está resuelta (cómo reserva el alumno exactamente) | Se asume reserva dentro del sistema con endpoint REST. La UI del alumno queda para el change de frontend. El backend expone endpoints claros. |

## Migration Plan

1. Agregar códigos de auditoría `COLOQUIO_CREAR`, `COLOQUIO_EDITAR`, `COLOQUIO_CERRAR`, `RESERVA_CREAR`, `RESERVA_CANCELAR`, `RESULTADO_REGISTRAR` en `audit_codes.py`
2. Agregar permisos `coloquios:gestionar` y `coloquios:reservar` en `permissions.py` y seeder de RBAC
3. Crear migración Alembic `f7a8b9c0d1e2_create_evaluacion_tables.py` con tablas `evaluaciones`, `dias_convocatoria`, `reservas_evaluacion`, `resultados_evaluacion`, y tabla puente `evaluacion_alumnos_convocados`
4. Implementar modelos → repositorios → services → schemas → routers
5. Escribir tests
6. Registrar el router en `app/main.py`

**Rollback**: `alembic downgrade -1` elimina las 4 tablas. Los permisos quedan en la tabla de permisos pero sin uso.

## Open Questions

- **Q1**: PA-14 — la reserva del alumno no está completamente especificada. El diseño asume reserva interna con cupo. Si en el futuro la reserva es externa (LMS), los endpoints de reserva sirven como API de integración.
- **Q2**: ¿Se necesita fecha/hora específica de reserva o solo fecha? El modelo E14 usa `fecha_hora` (datetime), pero para coloquios podría ser solo fecha. Se usa `fecha_hora` por consistencia con el modelo de datos.
- **Q3**: ¿El cupo es por día de convocatoria o por franja horaria? Por ahora es por día. El modelo `DiaConvocatoria` permite agregar franjas después.
