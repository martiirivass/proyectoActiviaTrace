## Context

Este change implementa el modelo, la API y el worker de la cola de comunicaciones del sistema. Se asienta sobre C-11 (análisis de atrasados) que ya provee el cómputo de alumnos atrasados por materia — ahora necesitamos el canal de comunicación saliente para notificarlos.

**Estado actual del codebase:**
- `Comunicacion` y `LoteComunicacion` no existen como modelos aún
- El código de auditoría `COMUNICACION_ENVIAR` ya está definido en `app/core/audit_codes.py`
- Los permisos `comunicacion:enviar` y `comunicacion:aprobar` ya están seedeados (C-04) con scope `global` para PROFESOR, COORDINADOR, ADMIN
- El worker es un placeholder no-op en `backend/app/workers/main.py` con loop asyncio de 60s
- El servicio `worker` en `docker-compose.yml` ya existe con `command: ["python", "-m", "app.workers.main"]`
- Patrón de repositorio: `TenantScopedRepository` con filtro de tenant automático
- Patrón de servicio: inyección de `AsyncSession` + `tenant_id`, delega a `AuditService` para logging
- `EncryptedString` type decorator disponible para cifrado AES-256 de campos PII
- Convención: snake_case, Pydantic `extra='forbid'`, soft delete con `SoftDeleteMixin`, ≤500 LOC/archivo

## Goals / Non-Goals

**Goals:**
- Modelar `Comunicacion` con ciclo de estados (RN-15), destinatario cifrado, agrupable por lote
- Modelar `LoteComunicacion` para agrupar envíos masivos con metadata de aprobación
- Implementar preview obligatorio antes de encolar (RN-16) — dos fases: vista previa → confirmación
- Endpoint para crear comunicaciones individuales (sin lote, procesables inmediatamente)
- Endpoint para crear comunicaciones masivas agrupadas en lote (requieren aprobación RN-17)
- Endpoint para aprobar o rechazar lotes completos (permiso `comunicacion:aprobar`)
- Endpoint para consultar estado de comunicaciones por lote, materia y destinatario
- Worker asíncrono que consume la cola: Pendiente → Enviando → Enviado/Error/Cancelado
- Integración SMTP para despacho real de emails
- Auditoría `COMUNICACION_ENVIAR` en cada envío exitoso y en aprobaciones
- Tests de ciclo de estados, preview, encolado, aprobación, worker dispatch, permisos

**Non-Goals:**
- Motor de plantillas con variables de sustitución (nombre del alumno, materia) — queda para iteración futura (S8 en KB)
- Configuración SMTP por tenant — se usa configuración global vía env vars
- Reintentos automáticos con backoff progresivo para mensajes Fallidos — implementación básica (1 intento + registro de error)
- Frontend de comunicaciones (C-22)
- Mensajería interna (bandeja del docente, F3.4) — es otra épica
- Tablón de avisos (F3.5) — es otra épica
- Integración con Moodle WS para envío de mensajes — solo email saliente

## Decisions

### D1 — Worker asyncio con polling, sin cola externa (Redis/ARQ/Celery)
**Decisión**: El worker usa un loop asyncio con polling a PostgreSQL cada N segundos, sin dependencia de Redis ni cola externa.
**Rationale**: 
- El placeholder ya está diseñado como asyncio loop. Migrar a Redis/ARQ agrega una dependencia infra compleja para el volumen actual (decenas, no millones de mensajes).
- PostgreSQL con polling es suficientemente performante para el throughput esperado (< 1000 msg/día por tenant).
- Se evita la complejidad operativa de Redis y la gestión de conexiones adicionales.
- Si el volumen escala, se puede migrar a ARQ + Redis sin cambiar el modelo de datos — solo el worker.
- Patrón consistente con la arquitectura async del proyecto (FastAPI + SQLAlchemy async).

### D2 — Lote como entidad separada (LoteComunicacion) con metadata de aprobación
**Decisión**: Se crea un modelo `LoteComunicacion` separado para agrupar envíos masivos, con estado propio (Pendiente/Aprobado/Rechazado) y metadata de quién y cuándo aprobó.
**Rationale**: 
- `lote_id` en `Comunicacion` es un UUID que referencia al lote. Tener una tabla separada permite almacenar metadata de aprobación sin contaminar el mensaje individual.
- Facilita consultas como "todos los mensajes de un lote" y "todos los lotes pendientes de aprobación".
- El flujo de aprobación (Parte B de FL-04) opera sobre lotes, no sobre mensajes individuales.

### D3 — Mensajes individuales sin lote → procesables inmediatamente; mensajes en lote → requieren aprobación
**Decisión**: `Comunicacion.lote_id` es nullable. Los mensajes sin lote (individuales) son procesables por el worker inmediatamente al pasar a Pendiente. Los mensajes con lote requieren que el lote esté en estado Aprobado para que el worker los procese.
**Rationale**: 
- RN-17 especifica aprobación solo para "envíos masivos". Un mensaje individual a un alumno no debería requerir aprobación de un COORDINADOR.
- El worker filtra con: `estado='Pendiente' AND (lote_id IS NULL OR lote_id IN (SELECT id FROM lotes WHERE estado='Aprobado'))`.
- La logica es simple y clara en una sola query.

### D4 — Preview en dos fases (crear preview → confirmar envío)
**Decisión**: El endpoint de preview (`POST /comunicaciones/preview`) recibe asunto + cuerpo + materia_id + lista de destinatarios y retorna una vista previa renderizada. El usuario revisa y confirma con `POST /comunicaciones/enviar` (que persiste y encola).
**Rationale**: 
- RN-16 exige preview obligatorio antes de cualquier envío.
- Separar preview de confirmación permite al usuario ver el contenido exacto antes de commitear.
- Consistente con el patrón de dos fases de importación de calificaciones (C-10).
- El preview no persiste nada — solo valida y retorna una representación.

### D5 — Sin motor de plantillas en este change
**Decisión**: El asunto y cuerpo se envían como texto plano/enriquecido fijo. No hay sustitución de variables por destinatario.
**Rationale**: 
- El KB menciona plantillas como supuesto (S8) pero ninguna user story de C-12 las requiere.
- Agregar un motor de templates (Jinja2, etc.) aumenta la superficie de este change sin necesidad inmediata.
- Se puede agregar en una iteración futura sin cambios de esquema (el cuerpo es un texto libre).

### D6 — Cifrado del destinatario con `EncryptedString` existente
**Decisión**: El campo `destinatario` (email del alumno) usa el type decorator `EncryptedString` del módulo `app.core.encrypted_types`.
**Rationale**: 
- Es el mecanismo establecido para PII en el sistema (DNI, CBU).
- Consistente con la regla dura #12: Secretos y PII siempre AES-256.
- El type decorator es transparente para la aplicación: se escribe/lee texto plano, la DB almacena cifrado.

### D7 — SMTP vía `aiosmtplib` con configuración global
**Decisión**: Se utiliza `aiosmtplib` como cliente SMTP asíncrono. Las credenciales SMTP se configuran via variables de entorno globales (no por tenant).
**Rationale**: 
- `aiosmtplib` es la librería async estándar para SMTP, compatible con el event loop de asyncio.
- Configuración global es suficiente para el MVP. Configuración por tenant se puede agregar con un modelo `TenantSmtpConfig` en el futuro.
- Las variables de entorno se definen en `settings.py` igual que `DATABASE_URL` y `SECRET_KEY`.

### D8 — Worker con transacciones por lote de mensajes
**Decisión**: El worker procesa mensajes en lotes (batch size configurable, default 20). Cada mensaje se actualiza individualmente (Enviando → Enviado/Error) para mantener granularidad de error.
**Rationale**: 
- Si un mensaje falla, no debe afectar a los demás del mismo lote.
- El batch size evita ocupar una transacción larga.
- Patrón de "un mensaje, una transacción" asegura consistencia sin bloqueos prolongados.

## Risks / Trade-offs

**[R1] Polling introduce latencia**
→ El worker revisa la BD cada N segundos (default 30s). Un mensaje puede tardar hasta N segundos en procesarse desde que se encola.
→ **Mitigación**: N es configurable vía env var `WORKER_POLL_INTERVAL`. Para uso inmediato se puede bajar a 5s. Para producción con alto volumen, migrar a notificaciones vía LISTEN/NOTIFY de PostgreSQL o Redis pub/sub.

**[R2] Sin reintentos automáticos para Fallidos**
→ Si el envío SMTP falla, el mensaje queda en estado Error y no se reintenta automáticamente.
→ **Mitigación**: Se registra el error en el mensaje (campo `error_msg` en Comunicacion para diagnóstico). Un endpoint de reencolado manual puede agregarse en el futuro.

**[R3] SMTP configuración global, no por tenant**
→ Si dos tenants usan distintos proveedores SMTP, no podrán configurarse independientemente.
→ **Mitigación**: Para MVP los tenants comparten la misma infraestructura SMTP (ej: SendGrid con subcuentas). Se puede extender con un modelo `TenantSmtpConfig` en el futuro sin cambios en el worker (solo lookup por tenant_id).

**[R4] Volumen de lotes grandes**
→ Un lote de 500 mensajes crea 500 filas en Comunicacion. El worker los procesa secuencialmente (o en lotes de 20).
→ **Mitigación**: El batch size configurable permite ajustar concurrencia. Si es necesario, se puede implementar procesamiento concurrente con `asyncio.gather()` limitado por semáforo.

## Migration Plan

1. Agregar dependencia `aiosmtplib` a `pyproject.toml`
2. Agregar configuraciones SMTP a `app.core.config` (env vars)
3. Crear modelos `Comunicacion` y `LoteComunicacion`
4. Agregar modelos al `__init__.py` de models
5. Generar migración Alembic
6. Crear repositorios `ComunicacionRepository` y `LoteComunicacionRepository`
7. Crear schemas Pydantic
8. Crear `ComunicacionService`
9. Crear routers en `/api/v1/comunicaciones/`
10. Registrar router en `main.py`
11. Reescribir `workers/main.py` con el worker real
12. Actualizar docker-compose si es necesario
13. Escribir tests

**Rollback**: `alembic downgrade -1` elimina tablas `comunicacion` y `lote_comunicacion`. El worker vuelve a su placeholder no-op. No hay pérdida de otros datos.

## Open Questions

- *(ninguna — el dominio de comunicaciones está cerrado en la KB)*
