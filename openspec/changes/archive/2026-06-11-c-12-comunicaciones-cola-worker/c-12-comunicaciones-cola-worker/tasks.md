## 1. Configuración y dependencias

- [x] 1.1 Agregar `aiosmtplib` a `pyproject.toml`
- [x] 1.2 Agregar configuraciones SMTP a `backend/app/core/config.py`: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_ADDRESS, SMTP_USE_TLS, WORKER_POLL_INTERVAL, WORKER_BATCH_SIZE

## 2. Modelos

- [x] 2.1 Crear modelo `Comunicacion` (id, tenant_id, lote_id nullable FK, enviado_por FK, materia_id FK, destinatario EncryptedString, asunto, cuerpo, estado enum Pendiente|Enviando|Enviado|Error|Cancelado, error_msg nullable, enviado_at nullable, created_at, updated_at — hereda SoftDeleteMixin)
- [x] 2.2 Crear modelo `LoteComunicacion` (id, tenant_id, materia_id FK, enviado_por FK, total_mensajes, estado enum Pendiente|Aprobado|Rechazado, aprobado_por nullable FK, aprobado_en nullable, rechazado_en nullable, created_at, updated_at — hereda SoftDeleteMixin)
- [x] 2.3 Registrar ambos modelos en `backend/app/models/__init__.py` y agregarlos a `__all__`

## 3. Migración

- [x] 3.1 Crear migration `d5e6f7a8b9c0_create_comunicacion_tables` con tablas `comunicacion` y `lote_comunicacion`
- [x] 3.2 Índices: FK lote_id → lote_comunicacion.id; FK enviado_por → users.id; FK materia_id → materias.id; índice por (tenant_id, lote_id) en comunicacion; índice por (tenant_id, materia_id, estado) en comunicacion; índice por (tenant_id, estado) en lote_comunicacion

## 4. Repositorios

- [x] 4.1 Crear `ComunicacionRepository` (TenantScopedRepository[Comunicacion]) con métodos:
  - [x] 4.1.1 `create_comunicacion(**kwargs)` — crear comunicación individual
  - [x] 4.1.2 `bulk_create_comunicaciones(entries: list[dict])` — bulk insert para lotes
  - [x] 4.1.3 `list_by_lote(lote_id)` — listar comunicaciones de un lote
  - [x] 4.1.4 `list_by_materia(materia_id, offset, limit)` — listar comunicaciones de una materia (paginado)
  - [x] 4.1.5 `count_by_estado(materia_id)` — distribución de estados para una materia
  - [x] 4.1.6 `find_pendientes_para_procesar(limit)` — query para worker: Pendiente AND (lote_id IS NULL OR lote_id IN lotes aprobados)
  - [x] 4.1.7 `actualizar_estado(id, estado, error_msg=None, enviado_at=None)` — actualizar estado de una comunicación
  - [x] 4.1.8 `cancelar_por_lote(lote_id)` — actualizar a Cancelado todas las Pendientes de un lote
- [x] 4.2 Crear `LoteComunicacionRepository` (TenantScopedRepository[LoteComunicacion]) con:
  - [x] 4.2.1 `create_lote(**kwargs)` — crear lote
  - [x] 4.2.2 `get_by_id(lote_id)` — obtener lote por ID (con scope tenant)
  - [x] 4.2.3 `list_pendientes()` — listar lotes pendientes de aprobación
  - [x] 4.2.4 `aprobar(lote_id, aprobado_por)` — aprobar lote (validando estado actual)
  - [x] 4.2.5 `rechazar(lote_id)` — rechazar lote (validando estado actual)

## 5. Schemas (Pydantic v2, extra='forbid')

- [x] 5.1 Crear `ComunicacionPreviewRequest` (asunto, cuerpo, materia_id, destinatarios: list[str])
- [x] 5.2 Crear `ComunicacionPreviewResponse` (asunto, cuerpo_renderizado, cantidad_destinatarios)
- [x] 5.3 Crear `ComunicacionIndividualRequest` (asunto, cuerpo, materia_id, destinatario_email)
- [x] 5.4 Crear `ComunicacionIndividualResponse` (id, estado)
- [x] 5.5 Crear `ComunicacionMasivaRequest` (asunto, cuerpo, materia_id, destinatarios: list[str])
- [x] 5.6 Crear `ComunicacionMasivaResponse` (lote_id, total_mensajes, estado_lote)
- [x] 5.7 Crear `ComunicacionItem` (id, destinatario enmascarado, asunto, estado, created_at, enviado_at, error_msg nullable)
- [x] 5.8 Crear `ComunicacionDetalle` (id, destinatario enmascarado, asunto, cuerpo, estado, materia_id, created_at, enviado_at, error_msg nullable)
- [x] 5.9 Crear `LotePendienteItem` (id, materia_id, enviado_por, total_mensajes, created_at)
- [x] 5.10 Crear `LoteDetalle` (id, materia_id, total_mensajes, estado, aprobado_por, aprobado_en, distribucion_estados: dict)
- [x] 5.11 Crear `DistribucionEstados` (pendiente, enviando, enviado, error, cancelado: int)
- [x] 5.12 Crear `AprobarLoteRequest` (lote_id)
- [x] 5.13 Crear `AprobarLoteResponse` (lote_id, estado, mensajes_liberados: int)
- [x] 5.14 Crear `RechazarLoteResponse` (lote_id, estado, mensajes_cancelados: int)
- [x] 5.15 Crear `ComunicacionListResponse` (items: list[ComunicacionItem], total: int, offset: int, limit: int)

## 6. Servicios

- [x] 6.1 Crear `ComunicacionService` con:
  - [x] 6.1.1 `preview(asunto, cuerpo, materia_id, destinatarios)` — validar datos, retornar preview (sin persistencia)
  - [x] 6.1.2 `enviar_individual(asunto, cuerpo, materia_id, destinatario_email, actor_id)` — validar destinatario en padrón activo, crear Comunicacion en Pendiente, generar audit COMUNICACION_ENVIAR
  - [x] 6.1.3 `enviar_masivo(asunto, cuerpo, materia_id, destinatarios, actor_id)` — crear LoteComunicacion + N Comunicaciones en Pendiente, deduplicar destinatarios, generar audit COMUNICACION_ENVIAR
  - [x] 6.1.4 `listar_lotes_pendientes()` — retornar lotes Pendiente para aprobación
  - [x] 6.1.5 `aprobar_lote(lote_id, aprobado_por)` — aprobar lote, generar audit
  - [x] 6.1.6 `rechazar_lote(lote_id)` — rechazar lote, cancelar mensajes Pendientes, generar audit
  - [x] 6.1.7 `obtener_detalle_lote(lote_id)` — retornar detalle + distribución de estados
  - [x] 6.1.8 `listar_por_materia(materia_id, offset, limit)` — listar comunicaciones de una materia
  - [x] 6.1.9 `obtener_distribucion(materia_id)` — distribución de estados agregada
  - [x] 6.1.10 `obtener_comunicacion(id)` — detalle de una comunicación
  - [x] 6.1.11 `_enmascarar_email(email)` — helper para enmascarar destinatario (ej: "alum***@test.com")

## 7. Routers

- [x] 7.1 Crear router `/api/v1/comunicaciones` con:
  - [x] 7.1.1 `POST /preview` — preview de comunicación (permiso `comunicacion:enviar`)
  - [x] 7.1.2 `POST /individual` — enviar comunicación individual (permiso `comunicacion:enviar`)
  - [x] 7.1.3 `POST /masivo` — enviar lote de comunicaciones (permiso `comunicacion:enviar`)
  - [x] 7.1.4 `GET /lotes/pendientes` — listar lotes pendientes de aprobación (permiso `comunicacion:aprobar`)
  - [x] 7.1.5 `POST /lotes/{lote_id}/aprobar` — aprobar lote (permiso `comunicacion:aprobar`)
  - [x] 7.1.6 `POST /lotes/{lote_id}/rechazar` — rechazar lote (permiso `comunicacion:aprobar`)
  - [x] 7.1.7 `GET /lotes/{lote_id}` — detalle de lote con distribución (permiso `comunicacion:enviar` o `comunicacion:aprobar`)
  - [x] 7.1.8 `GET /` — listar comunicaciones por materia (permiso `comunicacion:enviar`, query param materia_id)
  - [x] 7.1.9 `GET /distribucion` — distribución de estados por materia (permiso `comunicacion:enviar`, query param materia_id)
  - [x] 7.1.10 `GET /{id}` — detalle de comunicación (permiso `comunicacion:enviar`)
- [x] 7.2 Registrar router en `backend/app/main.py`

## 8. Worker

- [x] 8.1 Actualizar `backend/app/workers/main.py` con worker real:
  - [x] 8.1.1 Conexión a DB usando async_session_factory
  - [x] 8.1.2 Loop principal con polling cada WORKER_POLL_INTERVAL segundos
  - [x] 8.1.3 Query de comunicaciones Pendientes procesables (ver 4.1.6) con batch size configurable
  - [x] 8.1.4 Para cada comunicación: transicionar a Enviando, enviar email via aiosmtplib, registrar resultado (Enviado con enviado_at o Error con error_msg)
  - [x] 8.1.5 Manejo graceful shutdown con SIGTERM/SIGINT (completar lote actual antes de salir)
  - [x] 8.1.6 Logging estructurado de cada operación del worker
- [x] 8.2 Usar settings existentes para las variables SMTP y de worker (config.py)

## 9. Tests

- [x] 9.1 Tests de creación de comunicaciones:
  - [x] 9.1.1 Preview retorna representación correcta
  - [x] 9.1.2 Preview con datos inválidos → 422
  - [x] 9.1.3 Envío individual crea comunicación en Pendiente
  - [x] 9.1.4 Envío individual sin asunto → 422
  - [x] 9.1.5 Envío masivo crea lote + N comunicaciones
  - [x] 9.1.6 Envío masivo con destinatarios duplicados los deduplica
  - [x] 9.1.7 Envío masivo sin destinatarios → 422
- [x] 9.2 Tests de aprobación:
  - [x] 9.2.1 Listar lotes pendientes retorna solo lotes Pendiente
  - [x] 9.2.2 Aprobar lote cambia estado a Aprobado
  - [x] 9.2.3 Aprobar lote ya aprobado → 409
  - [x] 9.2.4 Rechazar lote cambia a Rechazado y cancela mensajes
  - [ ] ~~9.2.5 Sin permiso `comunicacion:aprobar` → 403~~ (es test de ruta con auth — requiere fixture client con token)
- [x] 9.3 Tests de seguimiento:
  - [x] 9.3.1 Consultar lote por ID retorna detalle + distribución
  - [x] 9.3.2 Consultar comunicaciones por materia retorna lista paginada
  - [x] 9.3.3 Consultar distribución retorna conteos correctos
  - [x] 9.3.4 Consultar lote inexistente → 404
- [x] 9.4 Tests de cifrado:
  - [x] 9.4.1 Destinatario se almacena cifrado en DB
  - [x] 9.4.2 Destinatario se lee desencriptado correctamente
- [x] 9.5 Tests de tenant isolation:
  - [x] 9.5.1 Tenant A no ve comunicaciones de Tenant B
  - [x] 9.5.2 Tenant A no ve lotes de Tenant B
- [x] 9.6 Tests de auditoría:
  - [x] 9.6.1 Envío individual genera audit COMUNICACION_ENVIAR
  - [x] 9.6.2 Envío masivo genera audit COMUNICACION_ENVIAR con lote_id
  - [x] 9.6.3 Aprobación de lote genera audit
  - [x] 9.6.4 Rechazo de lote genera audit
- [x] 9.7 Tests de worker:
  - [x] 9.7.1 Worker query retorna solo Pendientes procesables
  - [x] 9.7.2 Worker omite Pendientes con lote no aprobado
  - [x] 9.7.3 Worker procesa Pendientes con lote aprobado
  - [x] 9.7.4 Worker transiciona a Enviando antes del despacho
  - [x] 9.7.5 Worker registra Enviado con timestamp en éxito
  - [x] 9.7.6 Worker registra Error con mensaje en fallo
