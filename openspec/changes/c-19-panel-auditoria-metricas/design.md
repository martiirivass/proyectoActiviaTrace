## Context

El backend ya cuenta con el modelo `AuditLog` (E-AUD append-only), su repositorio (`AuditLogRepository` con método `find` básico), su servicio (`AuditService`) y un único endpoint `GET /audit/log` con filtros parciales (acción, actor, rango de fechas, paginación). También existe el modelo `Comunicacion` con sus estados (Pendiente/Enviando/Enviado/Error/Cancelado) que permite agregar por docente y materia.

**Lo que falta:**
- El endpoint `GET /audit/log` no acepta filtro por `materia_id`.
- No existe ningún endpoint de dashboard con métricas agregadas.
- `AuditLogRepository` no tiene métodos de agregación SQL (GROUP BY date, GROUP BY actor+materia).
- `AuditService` no tiene lógica de dashboard ni de scope `propio`.
- COORDINADOR no tiene el permiso `auditoria:ver` — necesita que se le asigne con scope `propio`.
- No hay schemas Pydantic para responses de dashboard.

**Stakeholders:** ADMIN (visión global), COORDINADOR (visión acotada a sus materias), FINANZAS (visión global existente).

## Goals / Non-Goals

**Goals:**
- Implementar el panel de interacciones (F9.1) con 4 sub-vistas en un solo response.
- Mejorar el log completo de auditoría (F9.2) con filtro por materia y límite configurable hasta 200.
- Agregar el permiso `auditoria:ver` con scope `propio` para COORDINADOR (RN-23: acceso según asignación).
- Mantener append-only sin modificar modelos existentes.
- Cobertura de tests ≥90% en reglas de negocio del módulo.

**Non-Goals:**
- NO se crean tablas nuevas — todo se resuelve con queries agregadas sobre `AuditLog` y `Comunicacion`.
- NO se modifican los modelos `AuditLog` ni `Comunicacion`.
- NO se implementa caché ni materialized views (el volumen de auditoría lo permite sin optimización temprana).
- NO se toca el frontend (eso es C-24).
- NO se agregan gráficos ni visualizaciones server-side (el frontend los arma con los datos agregados).

## Decisions

### ADR-019: Dashboard como un solo endpoint agregado

**Decisión:** `GET /api/audit/dashboard` devuelve las 4 sub-vistas en un solo response, no como endpoints separados.

**Razón:** El panel se renderiza completo — las 4 secciones son siempre visibles simultáneamente. Separar en 4 endpoints multiplica requests sin beneficio. Un solo response permite al frontend pintar todo el dashboard con una llamada. La payload no es pesada (∼50-200 registros por sección).

**Alternativa descartada:** 4 endpoints separados (`/audit/actions-by-day`, `/audit/comms-status`, etc.) — más flexibles pero más lentos en carga inicial y más costosos de cachear. Si en el futuro alguna sección es cara de calcular, se puede extraer como endpoint independiente sin breaking change (solo se agrega, no se quita del dashboard).

### ADR-020: Scope `propio` resuelto en Service, no en Repository

**Decisión:** `AuditService.get_dashboard()` recibe el scope del usuario actual y el `current_user` completo, y aplica el filtro de materias del coordinador a nivel de servicio antes de llamar al repositorio.

**Razón:** El scope `propio` requiere conocer las materias del usuario desde el módulo de asignaciones (C-07). El repositorio no debe tener conocimiento de permisos ni reglas de negocio. El servicio orquesta: (1) obtiene materias del coordinador desde `AsignacionRepository`, (2) si el scope es `propio`, filtra por esas materias, (3) delega al repositorio.

**Alternativa descartada:** Pasar lista de materias desde el router — el router no debe tener lógica de negocio. Pasarla desde el middleware — no existe tal middleware en la arquitectura actual.

### ADR-021: Agregaciones con SQLAlchemy 2.0 ORM, no SQL raw

**Decisión:** Las 4 consultas de agregación se implementan con SQLAlchemy 2.0 `select()`, `func.count()`, `func.date_trunc()`, `group_by()` sobre los modelos `AuditLog` y `Comunicacion` — sin SQL raw.

**Razón:** Consistencia con el resto del códigobase. SQLAlchemy 2.0 async maneja GROUP BY correctamente. Si en el futuro el volumen requiere optimización, se puede migrar a `text()` o vistas materializadas sin cambiar la interfaz del repositorio.

### ADR-022: Migración de seed, no alteración de migración existente

**Decisión:** Se crea una NUEVA migración Alembic que agrega el permiso `auditoria:ver` con scope `propio` al rol COORDINADOR. No se modifica la migración `a1b2c3d4e5f6`.

**Razón:** Las migraciones existentes ya corrieron en producción. Modificarlas viola la inmutabilidad del historial de migraciones.

**SQL de la migración:**
```sql
INSERT INTO role_permissions (id, role_id, permission_id, scope, tenant_id)
SELECT gen_random_uuid(), r.id, p.id, 'propio', r.tenant_id
FROM roles r, permissions p
WHERE r.name = 'COORDINADOR' AND p.name = 'auditoria:ver'
AND NOT EXISTS (
    SELECT 1 FROM role_permissions rp
    WHERE rp.role_id = r.id AND rp.permission_id = p.id
);
```

### ADR-023: Límite configurable en últimas acciones via query param

**Decisión:** El endpoint `GET /api/audit/log` acepta `limit` con rango `1-200`, default `50` (consistente con el comportamiento actual). El dashboard usa un límite fijo de 200 (default de F9.1) pero acepta override via query param.

**Razón:** El requerimiento F9.1 dice "máximo configurable; defecto 200 registros". Mantener el default del log general en 50 para paginación normal y 200 solo para el dashboard evita que consultas OLTP arrastren payloads grandes.

## Endpoints Planned

### `GET /api/audit/dashboard` — Panel de métricas agregadas

- **Guard:** `require_permission("auditoria:ver")`
- **Response (200):**
```json
{
  "acciones_por_dia": [
    {"fecha": "2026-06-01", "total": 45},
    {"fecha": "2026-06-02", "total": 32}
  ],
  "comunicaciones_por_docente": [
    {
      "docente_id": "uuid",
      "docente_nombre": "string",
      "pendiente": 5, "enviando": 2, "enviado": 30, "error": 1, "cancelado": 0
    }
  ],
  "interacciones_por_docente_materia": [
    {
      "docente_id": "uuid",
      "docente_nombre": "string",
      "materia_id": "uuid",
      "materia_nombre": "string",
      "total_acciones": 42,
      "acciones": {"CALIFICACIONES_IMPORTAR": 5, "COMUNICACION_ENVIAR": 20, ...}
    }
  ],
  "ultimas_acciones": [
    {
      "fecha_hora": "2026-06-15T10:30:00Z",
      "actor_id": "uuid",
      "materia_id": "uuid",
      "accion": "CALIFICACIONES_IMPORTAR",
      "filas_afectadas": 30,
      "ip": "192.168.1.1",
      "user_agent": "Mozilla/..."
    }
  ],
  "total": 200
}
```

### `GET /api/audit/log` — Log completo (mejorado)

- **Nuevo query param:** `materia_id: str | None`
- **Guard:** `require_permission("auditoria:ver")`
- **Scope `propio`:** si el usuario tiene scope `propio` en `auditoria:ver`, el servicio filtra automáticamente por las materias del usuario.

### Data Flow (dashboard)

```
Request → Router (guarda permisos)
       → Service.get_dashboard(current_user, filters)
           ├── _resolve_materias(current_user) → lista de materia_ids si scope=propio
           ├── Repo.count_actions_by_day(tenant_id, materia_ids?, desde?, hasta?)
           ├── Repo.count_comms_by_docente(tenant_id, materia_ids?, desde?, hasta?)
           ├── Repo.count_interactions_by_docente_materia(tenant_id, materia_ids?, desde?, hasta?)
           └── Repo.find_recent(tenant_id, materia_ids?, desde?, hasta?, limit=200)
       → Router → Response (ensamblado)
```

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| **Performance**: 4 queries agregadas simultáneas en un solo request podrían ser lentas con millones de registros de auditoría | Las tablas `audit_log` tienen índices en `tenant_id + fecha_hora`, `actor_id`, `materia_id`, `accion`. Si el volumen crece, se puede migrar a una sola query con múltiples CTEs o agregar un índice compuesto `(tenant_id, fecha_hora, accion)`. |
| **Scope `propio`**: obtener las materias de un coordinador agrega una query extra al dashboard | La query de asignaciones es liviana (índice por usuario_id + materia_id). Si hay muchos coordinadores con cientos de materias, se puede cachear. No se optimiza prematuremente. |
| **Estados de comunicación**: el endpoint de dashboard cruza datos de `Comunicacion` que pueden tener soft-delete | Se filtra con `deleted_at == None` consistente con el SoftDeleteMixin. |
| **Seguridad de datos**: el dashboard expone IPs y user-agents (PII sensible) | Solo ADMIN puede ver IP/user-agent completos. Para COORDINADOR, los campos IP y user-agent se omiten en el response del log detallado. |

## Migration Plan

1. **Nueva migración Alembic**: agrega `COORDINADOR → auditoria:ver (propio)`.
2. **Nuevos métodos en `AuditLogRepository`**: 4 métodos de agregación.
3. **Nuevos schemas en `schemas/audit.py`**: schemas del dashboard.
4. **Nuevo método en `AuditService`**: `get_dashboard()` + refactor menor de `get_log()` para soportar materia_id y scope.
5. **Nuevo endpoint + mejora del existente en `routers/audit.py`**.
6. **Tests**: cobertura completa del dashboard, del scope propio, y de los nuevos filtros.

**Rollback:** Revertir el commit y correr `alembic downgrade -1`.

## Open Questions

- *(ninguna — todas las decisiones están cerradas en el proposal aprobado)*
