## 1. Migración: Permiso auditoria:ver para COORDINADOR

- [x] 1.1 Crear nueva migración Alembic que asigne `auditoria:ver` con scope `propio` al rol COORDINADOR (idempotente, upsert condicional)
- [x] 1.2 Verificar que la migración es idempotente: ejecutar `alembic upgrade` dos veces sin errores ni duplicados

## 2. Repositorio: Nuevos métodos de agregación en AuditLogRepository

- [x] 2.1 Implementar `count_actions_by_day(tenant_id, materia_ids?, desde?, hasta?) -> list[dict]`: GROUP BY date_trunc('day', fecha_hora), ORDER BY fecha ASC
- [x] 2.2 Implementar `count_comms_by_docente(tenant_id, materia_ids?, desde?, hasta?) -> list[dict]`: cruce con Comunicacion, GROUP BY enviado_por, estado
- [x] 2.3 Implementar `count_interactions_by_docente_materia(tenant_id, materia_ids?, desde?, hasta?) -> list[dict]`: GROUP BY actor_id, materia_id, accion
- [x] 2.4 Implementar `find_recent(tenant_id, materia_ids?, desde?, hasta?, limit=200) -> list[AuditLog]`: ORDER BY fecha_hora DESC, límite configurable
- [x] 2.5 Modificar método `find()` existente para aceptar `materia_id` opcional como filtro adicional

## 3. Schemas: Dashboard response schemas en Pydantic v2

- [x] 3.1 Crear `AccionesPorDiaItem` schema: fecha (date), total (int)
- [x] 3.2 Crear `ComunicacionesPorDocenteItem` schema: docente_id, docente_nombre, pendiente, enviando, enviado, error, cancelado
- [x] 3.3 Crear `InteraccionesPorDocenteMateriaItem` schema: docente_id, docente_nombre, materia_id, materia_nombre, total_acciones, acciones (dict[str, int])
- [x] 3.4 Crear `UltimasAccionesItem` schema (reutiliza AuditLogResponse pero sin impersonado_id ni detalle completo)
- [x] 3.5 Crear `DashboardResponse` schema: compuesto con las 4 secciones + total

## 4. Servicio: Dashboard + scope propio en AuditService

- [x] 4.1 Implementar `get_dashboard(tenant_id, current_user, materia_id?, desde?, hasta?, limit?) -> DashboardResponse`
- [x] 4.2 Implementar método privado `_resolve_materias(current_user) -> list[UUID]`: consulta AsignacionRepository si scope es `propio`, retorna vacía si scope es `global`
- [x] 4.3 Integrar `_resolve_materias` en el filtro del dashboard: pasar materia_ids resueltos a los 4 métodos del repositorio
- [x] 4.4 Modificar `get_log()` para aceptar `materia_id` y aplicar scope `propio` igual que el dashboard
- [x] 4.5 Integrar resolución de nombres de docente y materia en el dashboard (joins con User y Materia)

## 5. Router: Endpoint dashboard + mejora log

- [x] 5.1 Agregar endpoint `GET /api/audit/dashboard` con guard `require_permission("auditoria:ver")` y query params: desde, hasta, materia_id, limit
- [x] 5.2 Modificar endpoint `GET /api/audit/log` existente para: (a) agregar query param `materia_id`, (b) elevar validación de limit a 200, (c) pasar current_user al service para scope propio
- [x] 5.3 Verificar que los endpoints existentes mantienen firma backward-compatible (mismos params = mismo comportamiento)

## 6. Tests: Dashboard

- [x] 6.1 Test: Admin obtiene dashboard completo con 4 secciones
- [x] 6.2 Test: Coordinador con scope propio ve solo sus materias en dashboard
- [x] 6.3 Test: Finanzas ve dashboard global (sin filtro de scope)
- [x] 6.4 Test: Usuario sin permiso `auditoria:ver` recibe 403
- [x] 6.5 Test: Dashboard con filtro de fechas (desde/hasta) limita resultados
- [x] 6.6 Test: Dashboard con materia_id filtra a esa materia
- [x] 6.7 Test: Dashboard limit por defecto = 200 en ultimas_acciones
- [x] 6.8 Test: Dashboard limit custom (50) funciona
- [x] 6.9 Test: Dashboard con rango vacío retorna arrays vacíos
- [x] 6.10 Test: `count_actions_by_day` agrupa correctamente por fecha
- [x] 6.11 Test: `count_comms_by_docente` agrupa por docente y estado
- [x] 6.12 Test: `count_interactions_by_docente_materia` agrupa por docente, materia y acción

## 7. Tests: Log mejorado

- [x] 7.1 Test: Log filter por materia_id funciona
- [x] 7.2 Test: Log materia_id inválido retorna 422
- [x] 7.3 Test: Log materia_id sin matches retorna array vacío
- [x] 7.4 Test: Coordinador con scope propio ve solo sus materias en log
- [x] 7.5 Test: Coordinador materia_id dentro de scope funciona
- [x] 7.6 Test: Coordinador materia_id fuera de scope retorna vacío
- [x] 7.7 Test: Log limit=200 aceptado (backward compatible)
- [x] 7.8 Test: Log limit por defecto sigue siendo 50
- [x] 7.9 Test: Log limit > 200 retorna 422
- [x] 7.10 Test: Filtros existentes (accion, actor_id, desde, hasta) siguen funcionando

## 8. Tests: Migración y permisos

- [x] 8.1 Test: Migración agrega `auditoria:ver(propio)` a COORDINADOR
- [x] 8.2 Test: Migración idempotente — ejecutar dos veces no duplica
- [x] 8.3 Test: ADMIN y FINANZAS mantienen `auditoria:ver(global)` sin cambios
- [x] 8.4 Test: Scope `propio` se resuelve desde AsignacionRepository
- [x] 8.5 Test: Scope `global` no agrega filtro de materias
