## Why

El flujo FL-04 (Envío masivo con aprobación) es el paso siguiente en el camino crítico después del análisis de atrasados (C-11). Sin el modelo `Comunicacion`, la cola de envíos y el worker asíncrono, el sistema no puede materializar el ciclo completo de detección → notificación a alumnos atrasados. Los permisos `comunicacion:enviar` y `comunicacion:aprobar` ya están seedeados (C-04), el código de auditoría `COMUNICACION_ENVIAR` ya existe (`audit_codes.py`), y el worker tiene un placeholder no-op. Este change implementa el modelo, la API REST y el worker real.

## What Changes

- Crear modelo `Comunicacion` con ciclo de estados Pendiente → Enviando → Enviado / Error / Cancelado (RN-15), agrupable por `lote_id`
- Crear modelo `LoteComunicacion` para agrupar envíos masivos de una misma acción con metadata de aprobación
- Endpoints para crear comunicaciones individuales o masivas con vista previa obligatoria antes de encolar (RN-16, F3.1)
- Endpoint para aprobar o rechazar lotes completos de comunicaciones (RN-17, F3.3)
- Endpoint para consultar estado de comunicaciones por lote, materia y destinatario (F3.2 tracking)
- Worker asíncrono que consume la cola: procesa comunicaciones en estado Pendiente → Enviando, despacha email vía SMTP, registra resultado (Enviado/Error) o permite cancelación
- Cifrado AES-256 del campo `destinatario` (email del alumno) usando `EncryptedString` existente
- Log de auditoría `COMUNICACION_ENVIAR` en cada envío y aprobación
- Migración Alembic: tablas `comunicacion` y `lote_comunicacion`
- El worker Docker ya existe como servicio en `docker-compose.yml` — se actualiza su entrypoint para que corra el worker real

## Capabilities

### New Capabilities
- `comunicaciones-enviar`: Creación de comunicaciones individuales o masivas con preview obligatorio antes de encolar (RN-16). El mensaje se persiste en estado Pendiente. Soporta redacción de asunto y cuerpo, destinatario desde padrón de la materia. Permiso `comunicacion:enviar`.
- `comunicaciones-aprobar`: Aprobación o rechazo de lotes de comunicaciones masivas. El aprobador (con permiso `comunicacion:aprobar`) puede aprobar un lote completo o rechazarlo. Los mensajes aprobados transicionan a Enviando; los rechazados quedan como Cancelado (RN-17, FL-04 Parte B).
- `comunicaciones-seguimiento`: Consulta de estado de comunicaciones por lote, materia o destinatario. Expone distribución de estados (Pendiente / Enviando / Enviado / Error / Cancelado) y permite tracking granular (F3.2).

### Modified Capabilities
- *(ninguna — son capabilities nuevas)*

## Impact

- **Nuevos modelos**: `Comunicacion`, `LoteComunicacion` en `backend/app/models/`
- **Nuevo repositorio**: `ComunicacionRepository` scoped por tenant (tenant_id en todos los queries), `LoteComunicacionRepository`
- **Nuevo servicio**: `ComunicacionService` con lógica de:
  - Creación de comunicaciones con preview (validación y persistencia en Pendiente)
  - Encolado masivo con agrupación por lote
  - Aprobación/rechazo de lotes
  - Consulta de estado y tracking
- **Nuevo worker**: actualización de `backend/app/workers/main.py` de placeholder no-op a worker real que:
  - Polling de comunicaciones en estado Pendiente
  - Transición a Enviando
  - Despacho SMTP con reintentos
  - Registro de resultado (Enviado/Error)
  - Soporte de cancelación
- **Nuevos schemas**: Pydantic v2 con `extra='forbid'` para creación, preview, aprobación y consulta de comunicaciones
- **Nuevos routers**: `/api/v1/comunicaciones/*` con permisos `comunicacion:enviar` y `comunicacion:aprobar`
- **Migración**: Alembic con tablas `comunicacion` y `lote_comunicacion`
- **Dependencias nueva**: librería SMTP/email (`aiosmtplib` o similar) para envío desde el worker
- **Config**: variables de entorno SMTP (host, puerto, usuario, password, from address) en settings
- **Tests**: creación con preview, encolado masivo, aprobación de lote, ciclo de estados, cifrado de destinatario, worker dispatch, permisos
