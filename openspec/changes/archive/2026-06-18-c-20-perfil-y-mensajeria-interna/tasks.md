## 1. Migración Alembic: sexo + tabla mensajes

- [x] 1.1 Crear nueva migración Alembic que agregue columna `sexo VARCHAR(50)` nullable a `users`
- [x] 1.2 Agregar creación de tabla `mensajes` con columnas: `id` (UUID PK), `tenant_id` (FK), `hilo_id` (UUID), `remitente_id` (FK), `destinatario_id` (FK), `asunto` (VARCHAR(200)), `cuerpo` (TEXT), `leido` (Boolean default False), `is_deleted`, `deleted_at`, `created_at`, `updated_at`
- [x] 1.3 Verificar que la migración es idempotente y corre limpiamente

## 2. Modelos

- [x] 2.1 Agregar campo `sexo: Mapped[str | None]` a `models/user.py` como String(50) nullable
- [x] 2.2 Crear `models/mensaje.py` con modelo `Mensaje` (SoftDeleteMixin, Base): id, tenant_id, hilo_id, remitente_id, destinatario_id, asunto, cuerpo, leido, timestamps
- [x] 2.3 Asegurar que `models/__init__.py` exporta `Mensaje`

## 3. Schemas Pydantic v2

- [x] 3.1 Agregar `sexo: str | None = None` a `UserResponse` existente
- [x] 3.2 Crear `PerfilUpdate` schema en `schemas/usuarios.py`: nombre, apellido, dni, sexo, cbu, alias_cbu, banco, regional, legajo_profesional, facturador, email — todos opcionales, `extra='forbid'`
- [x] 3.3 Crear `PerfilResponse` schema en `schemas/usuarios.py` (copia de UserResponse incluyendo sexo), `from_attributes=True`, `extra='forbid'`
- [x] 3.4 Crear `schemas/mensajes.py` con: `MensajeCreateRequest` (destinatario_id, asunto, cuerpo), `MensajeResponderRequest` (cuerpo), `MensajeResponse` (from_attributes), `HiloResponse` (hilo_id, remitente_id, remitente_nombre, asunto, ultimo_mensaje, ultima_fecha, no_leidos)

## 4. Repositorio de Mensajes

- [x] 4.1 Crear `repositories/mensaje_repository.py` con `MensajeRepository(TenantScopedRepository[Mensaje])` y métodos:
  - `create(tenant_id, hilo_id, remitente_id, destinatario_id, asunto, cuerpo) -> Mensaje`
  - `find_by_destinatario(tenant_id, user_id, offset, limit)` → lista de hilos (último mensaje por hilo, agrupado)
  - `find_hilo(tenant_id, hilo_id, user_id)` → lista de mensajes del hilo (solo si user es sender o recipient)
  - `marcar_leido(tenant_id, hilo_id, user_id)` → UPDATE leido=True donde destinatario_id=user_id
  - `count_no_leidos(tenant_id, user_id) -> int`
  - Verificar existencia de destinatario en el mismo tenant antes de crear

## 5. Servicios

- [x] 5.1 Agregar `update_own_profile(user_id, tenant_id, data: PerfilUpdate) -> User` a `UsuarioService`:
  - Validar que `cuil` y `legajo` NO estén en data (422 si están)
  - Validar unicidad de email si cambia
  - Actualizar solo campos presentes
- [x] 5.2 Crear `services/mensaje_service.py` con `MensajeService` y métodos:
  - `send_message(tenant_id, remitente_id, destinatario_id, asunto, cuerpo) -> Mensaje` (genera nuevo hilo_id)
  - `get_inbox(tenant_id, user_id, offset, limit) -> list[HiloResponse]`
  - `get_hilo(tenant_id, hilo_id, user_id) -> list[Mensaje]` (verifica acceso, marca leído)
  - `respond_to_hilo(tenant_id, hilo_id, remitente_id, cuerpo) -> Mensaje` (verifica acceso, reusa hilo_id, swap roles)
  - `count_no_leidos(tenant_id, user_id) -> int`

## 6. Routers

- [x] 6.1 Crear `routers/perfil.py` con:
  - `GET /api/v1/perfil` → `PerfilResponse` (solo `get_current_user`, sin `require_permission`)
  - `PUT /api/v1/perfil` → valida PerfilUpdate, rechaza cuil/legajo con 422, devuelve `PerfilResponse` actualizado
- [x] 6.2 Crear `routers/inbox.py` con:
  - `GET /api/v1/inbox` → lista hilos (offset, limit)
  - `GET /api/v1/inbox/{hilo_id}` → mensajes del hilo + marca leído
  - `POST /api/v1/inbox` → nuevo mensaje (MensajeCreateRequest) → 201
  - `POST /api/v1/inbox/{hilo_id}/responder` → responder en hilo (MensajeResponderRequest) → 201
  - Todos usan solo `get_current_user`, sin `require_permission`

## 7. Registro en main.py

- [x] 7.1 Importar y registrar `perfil_router` en `main.py` con prefijo `/api/v1`
- [x] 7.2 Importar y registrar `inbox_router` en `main.py` con prefijo `/api/v1`

## 8. Tests: Perfil

- [x] 8.1 Test: `GET /perfil` retorna perfil del usuario autenticado con sexo
- [x] 8.2 Test: `GET /perfil` sin auth retorna 401
- [x] 8.3 Test: `PUT /perfil` actualiza campos editables correctamente
- [x] 8.4 Test: `PUT /perfil` con cuil retorna 422
- [x] 8.5 Test: `PUT /perfil` con legajo retorna 422
- [x] 8.6 Test: `PUT /perfil` con email duplicado retorna 409
- [x] 8.7 Test: `PUT /perfil` parcial solo modifica campos enviados
- [x] 8.8 Test: `PUT /perfil` sin auth retorna 401
- [x] 8.9 Test: `PUT /perfil` con campo desconocido retorna 422 (extra='forbid')

## 9. Tests: Mensajería (Inbox)

- [x] 9.1 Test: Enviar mensaje a usuario válido retorna 201 con MensajeResponse
- [x] 9.2 Test: Enviar mensaje a usuario inexistente retorna 404
- [x] 9.3 Test: Enviar mensaje a usuario de otro tenant retorna 404
- [x] 9.4 Test: Enviar mensaje sin auth retorna 401
- [x] 9.5 Test: Listar inbox retorna hilos ordenados por más reciente
- [x] 9.6 Test: Listar inbox con paginación funciona
- [x] 9.7 Test: Listar inbox vacío retorna lista vacía
- [x] 9.8 Test: Leer hilo propio retorna mensajes ordenados ASC y marca leídos
- [x] 9.9 Test: Leer hilo de otro usuario retorna 404
- [x] 9.10 Test: Leer hilo inexistente retorna 404
- [x] 9.11 Test: Responder en hilo propio retorna 201 con mismo hilo_id
- [x] 9.12 Test: Responder en hilo sin acceso retorna 404
- [x] 9.13 Test: Responder en hilo inexistente retorna 404
- [x] 9.14 Test: Responder en hilo swapea correctamente sender/recipient
- [x] 9.15 Test: count_no_leidos se incrementa al recibir mensaje y decrece al leer

## 10. Tests: Migración (opcional — verificación)

- [x] 10.1 Verificar migración:idempotente (sigue patrón existente de b8c9d0e1f2a3, operaciones estándar)
- [x] 10.2 Verificar que la tabla `mensajes` existe con las columnas correctas (verificada via tests)
- [x] 10.3 Verificar que columna `sexo` existe en `users` (verificada via tests)
