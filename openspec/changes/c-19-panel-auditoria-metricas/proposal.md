## Why

El sistema ya cuenta con un log de auditoría append-only (C-05) que registra cada acción significativa, pero solo existe un endpoint lineal `GET /audit/log` sin capacidades de agregación ni dashboard. ADMIN y COORDINADOR no tienen visibilidad del volumen de uso del sistema, del estado de las comunicaciones por docente, ni de métricas de interacción que permitan supervisar la actividad del equipo docente. Sin este panel, la auditoría es un volcado de datos sin valor gerencial — datos sin contexto no son información.

## What Changes

- **Nuevo endpoint `/api/audit/dashboard`**: agrega métricas de uso en un solo response (acciones por día, estado de comunicaciones por docente, interacciones por docente×materia, últimas acciones).
- **Mejora del endpoint `GET /api/audit/log`**: agrega filtro por `materia_id`, eleva el `limit` máximo a 200 (default), y soporta scope `propio` para COORDINADOR.
- **Nuevo permiso `auditoria:ver` con scope `propio` para COORDINADOR**: migración que agrega la asignación faltante. Hoy COORDINADOR no tiene `auditoria:ver` en la seed — se añade con scope `propio`.
- **Nuevos métodos en `AuditLogRepository`**: consultas de agregación SQL (GROUP BY date, GROUP BY actor+materia, GROUP BY estado comunicación).
- **Nuevos schemas Pydantic v2** para responses del dashboard.
- **No se modifican modelos** — el `AuditLog` y `Comunicacion` existentes son suficientes.
- **No se crean nuevas tablas** — todo se resuelve con queries agregadas sobre tablas existentes.

## Capabilities

### New Capabilities
- `audit-dashboard`: Panel de métricas agregadas del sistema — acciones por día, estado de comunicaciones por docente, interacciones por docente×materia, últimas acciones con límite configurable.
- `audit-log-enhanced`: Log completo de auditoría con filtro por materia, límite configurable hasta 200 registros, y scope `propio` para COORDINADOR.
- `coordinator-audit-scope`: Permiso `auditoria:ver` con scope `propio` para el rol COORDINADOR (nueva migración de seed).

### Modified Capabilities
- *(ninguna — los specs existentes en `openspec/specs/` no cubren auditoría)*

## Impact

- **Backend** (`audit_log_repository.py`): +4 métodos de agregación SQL.
- **Backend** (`audit_service.py`): nuevo método `get_dashboard()` con lógica de scope `propio`.
- **Backend** (`routers/audit.py`): nuevo endpoint `GET /audit/dashboard`, mejora `GET /audit/log` con `materia_id`.
- **Backend** (`schemas/audit.py`): +3 schemas de response para dashboard.
- **Backend** (migración Alembic): nuevo seed `COORDINADOR → auditoria:ver (propio)`.
- **Dependencias**: C-05 (audit-log) y C-07 (usuarios-y-asignaciones) deben estar completos — ambos lo están.
- **No breaking**: todos los endpoints existentes mantienen firma backward-compatible.
