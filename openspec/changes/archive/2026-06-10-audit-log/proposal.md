## Why

El sistema exige auditoría obligatoria para toda acción significativa (RN del modelo de datos #6). Sin un log de auditoría estructurado, no es posible trazabilidad de quién hizo qué, cuándo y en contexto de qué tenant. Esto es requisito legal/funcional para una plataforma multi-tenant de gestión académica.

Además, la funcionalidad de impersonación (suplantación legítima) requiere registro explícito de inicio/fin y que toda acción bajo impersonación quede atribuida al actor real. Sin el modelo de auditoría no se puede implementar impersonación de forma segura.

## What Changes

- Crear modelo `AuditLog` (append-only, inmutable) con todos los campos definidos en E-AUD
- Crear repositorio `AuditLogRepository` con solo inserción y consulta (sin update/delete)
- Crear servicio `AuditService` con método `log(...)` y helpers por acción
- Crear enum/dicc de códigos de acción estandarizados
- Crear middleware de auditoría opcional (log automático de requests)
- Crear endpoint GET para consultar el log (solo lectura, con filtros)
- Agregar soporte para impersonación: registrar `impersonado_id`
- Migration 004: tabla `audit_log`

## Capabilities

### New Capabilities
- `audit-log`: Registro inmutable de acciones significativas, consulta con filtros, y soporte para impersonación

### Modified Capabilities
- *(ninguna — es capability nueva)*

## Impact

- **Nuevo modelo**: `AuditLog` en `backend/app/models/audit_log.py`
- **Nuevo repositorio**: `AuditLogRepository` en `backend/app/repositories/audit_log.py`
- **Nuevo servicio**: `AuditService` en `backend/app/services/audit_service.py`
- **Nuevo router**: GET `/api/v1/audit/log` en `backend/app/api/v1/routers/audit.py`
- **Middleware**: opcional en `backend/app/core/audit_middleware.py`
- **Migración**: Alembic 004_create_audit_log_table
- **Códigos de acción**: archivo de constantes en `backend/app/core/audit_codes.py`
