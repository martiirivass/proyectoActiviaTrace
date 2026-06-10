## 1. Extensión de Repository

- [x] 1.1 Agregar filtro `dictado_id` a `AsignacionRepository.list()`
- [x] 1.2 Agregar filtros por `carrera_id` y `cohorte_id` (join a Dictado) al `list()`
- [x] 1.3 Agregar método `list_by_dictado(dictado_id)` para obtener asignaciones de un equipo
- [x] 1.4 Agregar método `bulk_create(asignaciones: list[dict])` para creación masiva
- [x] 1.5 Agregar método `update_vigencia(dictado_id, desde, hasta)` para actualización en bloque
- [x] 1.6 Agregar método `count_by_dictado(dictado_id)` para verificar existencia

## 2. Extensiones de Service

- [x] 2.1 Agregar método `mis_equipos(usuario_id, estado, rol)` con filtros opcionales
- [x] 2.2 Agregar método `asignar_masivo(dictado_id, rol, desde, hasta, usuario_ids)` con transacción atómica
- [x] 2.3 Agregar método `clonar_equipo(dictado_origen_id, dictado_destino_id, force)` con validaciones y transacción
- [x] 2.4 Agregar método `modificar_vigencia_general(dictado_id, desde, hasta)` con validación de fechas
- [x] 2.5 Agregar método `exportar_equipo(dictado_id)` para generar filas CSV

## 3. Nuevos Schemas

- [x] 3.1 Crear `AsignacionMasivaRequest` con `dictado_id`, `rol`, `desde`, `hasta`, `usuario_ids: list[UUID]`
- [x] 3.2 Crear `ClonarEquipoRequest` con `dictado_origen_id`, `dictado_destino_id`, `force: bool = False`
- [x] 3.3 Crear `VigenciaUpdateRequest` con `desde: date`, `hasta: date`
- [x] 3.4 Crear `AsignacionConDictadoResponse` (asignación + datos anidados del dictado)

## 4. Nuevo Router /api/v1/equipos/

- [x] 4.1 Crear `backend/app/api/v1/routers/equipos.py` con router `equipos_router`
- [x] 4.2 Endpoint GET `/mis-equipos` — sin `require_permission`, filtra por usuario autenticado
- [x] 4.3 Endpoint GET `/asignaciones` — listado con filtros (dictado, carrera, rol) + paginación
- [x] 4.4 Endpoint POST `/masiva` — asignación masiva atómica, requiere `equipos:asignar`
- [x] 4.5 Endpoint POST `/clonar` — clonación de equipo, requiere `equipos:asignar`
- [x] 4.6 Endpoint PUT `/{dictado_id}/vigencia` — modificar vigencia general, requiere `equipos:asignar`
- [x] 4.7 Endpoint GET `/{dictado_id}/exportar` — exportar CSV, requiere `equipos:asignar`
- [x] 4.8 Integrar `equipos_router` en `main.py`

## 5. Audit Logging

- [x] 5.1 Verificar que `ASIGNACION_MODIFICAR` ya existe en `audit_codes.py`
- [x] 5.2 Integrar audit en `asignar_masivo()`: log con dictado_id, rol, cantidad
- [x] 5.3 Integrar audit en `clonar_equipo()`: log con origen, destino, cantidad
- [x] 5.4 Integrar audit en `modificar_vigencia_general()`: log con dictado_id, fechas, cantidad

## 6. Tests

- [x] 6.1 Test: mis equipos devuelve solo asignaciones del usuario autenticado
- [x] 6.2 Test: mis equipos sin asignaciones devuelve lista vacía
- [x] 6.3 Test: mis equipos con filtro por estado/rol
- [x] 6.4 Test: asignación masiva exitosa
- [x] 6.5 Test: asignación masiva con usuario duplicado → 422 + no se crea nada
- [x] 6.6 Test: asignación masiva con usuario inválido → 422
- [x] 6.7 Test: asignación masiva sin permiso → 403
- [x] 6.8 Test: clonar equipo exitoso
- [x] 6.9 Test: clonar con destino ocupado → 409
- [x] 6.10 Test: clonar forzado con destino ocupado → 201
- [x] 6.11 Test: clonar con origen sin asignaciones → lista vacía
- [x] 6.12 Test: clonar sin permiso → 403
- [x] 6.13 Test: modificar vigencia general exitoso
- [x] 6.14 Test: modificar vigencia con fecha inválida → 422
- [x] 6.15 Test: exportar equipo genera CSV
- [x] 6.16 Test: exportar equipo sin datos genera CSV con solo headers
- [x] 6.17 Test: audit log generado en cada operación de escritura
