## Context

El backend ya cuenta con:
- Modelo `User` con PII cifrada, CRUD admin en `admin_usuarios.py` (requiere `usuarios:gestionar`), y `UsuarioService`/`UsuarioRepository` con operaciones básicas.
- Sistema de autenticación JWT con `get_current_user` que provee `CurrentUser` con `id`, `email`, `tenant_id`, `roles`.
- Permisos RBAC con `require_permission` guard.

**Lo que falta:**
- No existe un endpoint de perfil público (`GET /perfil`, `PUT /perfil`) que el propio usuario pueda consultar/editar sin permisos de admin.
- El modelo `User` no tiene campo `sexo` (necesario para F11.1).
- No existe modelo `Mensaje` ni tabla de mensajería interna.
- No hay endpoints de inbox para mensajería entre usuarios registrados.
- No hay agrupación por hilos ni marcado de leído.

**Stakeholders:** cualquier usuario autenticado del sistema — TUTOR, PROFESOR, COORDINADOR, ADMIN, FINANZAS, NEXO.

## Goals / Non-Goals

**Goals:**
- Implementar `GET /api/v1/perfil` y `PUT /api/v1/perfil` para que cualquier usuario autenticado lea/edite su propio perfil.
- Agregar columna `sexo` al modelo `User` (String(50), nullable).
- Implementar modelo `Mensaje` con tabla `mensajes` y agrupación por `hilo_id`.
- Implementar inbox: listar hilos, leer hilo, enviar mensaje nuevo, responder en hilo.
- Migración Alembic: `sexo` + `mensajes`.
- Cobertura de tests ≥90% en reglas de negocio del módulo.

**Non-Goals:**
- NO se implementan notificaciones push ni email notifications al recibir un mensaje.
- NO se implementa búsqueda global de mensajes.
- NO se implementan mensajes grupales ni broadcast.
- NO se implementan archivos adjuntos en mensajes.
- NO se implementa borrado de mensajes (ni soft ni hard — el modelo usa SoftDeleteMixin por consistencia pero no se expone en API).
- NO se implementa un sistema de "en línea" / "presencia".
- NO se modifica el endpoint `GET /me` existente en auth — el perfil completo va en `/api/v1/perfil`.

## Decisions

### ADR-024: Un solo modelo Mensaje con hilo_id para threading

**Decisión:** Se crea un único modelo `Mensaje` con un campo `hilo_id` (UUID) que agrupa mensajes del mismo hilo. No hay tabla separada `Hilo`.

**Razón:** La mensajería interna entre usuarios registrados no necesita metadatos de hilo (asunto del hilo, participantes, etc.) — cada mensaje lleva su propio `asunto`. El hilo es simplemente un conjunto de mensajes que comparten el mismo `hilo_id`. Esto simplifica el modelo, evita una tabla extra y reduce la complejidad de las queries. El primer mensaje de una conversación genera un `hilo_id` nuevo; las respuestas reusan el mismo.

**Alternativa descartada:** Tabla `Hilo` separada con relación 1:N a `Mensaje` — más normalizada pero innecesaria para el alcance actual (sin metadatos de hilo). Se puede migrar si en el futuro se necesitan features como "archivar hilo", "asunto del hilo editable", o "participantes del hilo".

### ADR-025: Perfil update con validación en Service, no en Schema

**Decisión:** `PerfilUpdate` schema acepta todos los campos potencialmente editables, pero `UsuarioService.update_own_profile()` rechaza explícitamente `cuil` y `legajo` con 422 si están presentes.

**Razón:** `cuil` y `legajo` son campos de solo lectura para el usuario (F11.1). Rechazar en Service permite un mensaje de error semántico ("El campo CUIL no es modificable") en lugar de simplemente ignorar el campo. El schema acepta los campos para poder devolver un error informativo, no solo silenciar el cambio.

**Alternativa descartada:** Excluir `cuil`/`legajo` del schema `PerfilUpdate` — el usuario recibiría un error genérico de campo desconocido (por `extra='forbid'`) sin saber por qué. Peor experiencia de usuario.

### ADR-026: Sin permiso especial para perfil ni inbox

**Decisión:** Los endpoints de perfil e inbox NO requieren `require_permission(...)`. Cualquier usuario autenticado (tiene JWT válido) puede usar ambos.

**Razón:** F11.1 dice explícitamente "cualquier usuario autenticado". F11.2 también. F3.4 restringe a ciertos roles, pero F11.2 (Épica 11) amplía a todos. Prevalece la definición más reciente e inclusiva. Además, el acceso está naturalmente acotado: el perfil solo muestra/edita los datos del propio usuario, y el inbox solo muestra mensajes donde el usuario es remitente o destinatario.

**Alternativa descartada:** Agregar permisos `perfil:ver`, `perfil:editar`, `mensajes:enviar` — sobreingeniería para un caso donde el scope es inherentemente `propio` (el usuario solo opera sobre sus propios datos).

### ADR-027: hilo_id como UUID lógico, no FK

**Decisión:** `hilo_id` es un campo UUID en `Mensaje` sin foreign key a otra tabla. Se genera con `uuid.uuid4()` para el primer mensaje de un hilo y se reusa en las respuestas.

**Razón:** No existe una tabla `Hilo` a la que referenciar (ADR-024). El UUID es un identificador lógico que agrupa mensajes. La consistencia referencial se mantiene a nivel de aplicación: el service verifica que el `hilo_id` exista antes de permitir una respuesta.

### ADR-028: Marcado de leído por hilo, no por mensaje individual

**Decisión:** `marcar_leido(tenant_id, hilo_id, user_id)` marca TODOS los mensajes no leídos de un hilo como leídos para ese usuario. No hay endpoint para marcar un mensaje individual.

**Razón:** Cuando un usuario abre un hilo, se asume que leyó todos los mensajes. El marcado individual sería más granular pero agrega complejidad innecesaria. Si en el futuro se necesita tracking por mensaje, se puede migrar.

### ADR-029: Reuso de UsuarioRepository — sin repositorio separado de perfil

**Decisión:** El perfil reusa `UsuarioRepository` existente. `UsuarioService` obtiene un nuevo método `update_own_profile()` que valida readonly fields antes de delegar al repo.

**Razón:** No hay lógica de persistencia distinta para el perfil vs usuario admin — ambos operan sobre la misma tabla `users`. Crear un repositorio separado sería duplicación. La diferencia está únicamente en la validación (service) y en el schema (qué campos se exponen).

## Endpoints Planned

### `GET /api/v1/perfil` — Leer perfil propio

- **Guard:** solo autenticación (`get_current_user`)
- **Response (200):** `PerfilResponse` (hereda de `UserResponse` + `sexo`)
- **Response (401):** si no hay JWT válido

### `PUT /api/v1/perfil` — Actualizar perfil propio

- **Guard:** solo autenticación (`get_current_user`)
- **Request body:** `PerfilUpdate` — campos editables
- **Response (200):** `PerfilResponse` actualizado
- **Response (422):** si incluye `cuil` o `legajo` (con mensaje específico)
- **Response (409):** si el email ya está en uso por otro usuario del mismo tenant

### `GET /api/v1/inbox` — Listar hilos

- **Guard:** solo autenticación
- **Response (200):** `list[HiloResponse]` — último mensaje por hilo + cantidad no leídos
- **Query params:** `offset`, `limit`

### `GET /api/v1/inbox/{hilo_id}` — Leer hilo

- **Guard:** solo autenticación (verifica que el usuario sea remitente o destinatario de al menos un mensaje del hilo)
- **Response (200):** `list[MensajeResponse]` ordenado por created_at ASC
- **Side effect:** marca todos los mensajes del hilo como leídos para el usuario

### `POST /api/v1/inbox` — Enviar nuevo mensaje

- **Guard:** solo autenticación
- **Request body:** `MensajeCreateRequest` (`destinatario_id`, `asunto`, `cuerpo`)
- **Response (201):** `MensajeResponse`
- **Response (404):** si `destinatario_id` no existe en el mismo tenant

### `POST /api/v1/inbox/{hilo_id}/responder` — Responder en hilo

- **Guard:** solo autenticación (verifica que el usuario sea remitente o destinatario del hilo)
- **Request body:** `MensajeResponderRequest` (`cuerpo`)
- **Response (201):** `MensajeResponse`
- **Response (404):** si el hilo no existe o el usuario no tiene acceso

### Data Model

```python
class Mensaje(SoftDeleteMixin, Base):
    __tablename__ = "mensajes"
    
    id: UUID (PK, default uuid4)
    tenant_id: UUID (FK → tenants, NOT NULL, indexed)
    hilo_id: UUID (NOT NULL, indexed — shared across thread)
    remitente_id: UUID (FK → users, NOT NULL)
    destinatario_id: UUID (FK → users, NOT NULL)
    asunto: String(200, NOT NULL)
    cuerpo: Text (NOT NULL)
    leido: Boolean (default False, NOT NULL)
    created_at: DateTime (server_default now)
    updated_at: DateTime (onupdate now)
```

### Data Flow (inbox)

```
Request → Router (valida autenticación)
       → MensajeService
           ├── send_message(tenant_id, remitente_id, destinatario_id, asunto, cuerpo)
           │   ├── Genera nuevo hilo_id (UUID4)
           │   └── Repo.create(...)
           ├── get_inbox(tenant_id, user_id, offset, limit)
           │   └── Repo.find_by_destinatario(...)
           ├── get_hilo(tenant_id, hilo_id, user_id)
           │   ├── Repo.find_hilo(...) — verifica acceso
           │   └── Repo.marcar_leido(...)
           ├── respond_to_hilo(tenant_id, hilo_id, remitente_id, cuerpo)
           │   ├── Repo.find_hilo(...) — verifica acceso
           │   └── Repo.create(hilo_id existing)
           └── count_no_leidos(tenant_id, user_id)
               └── Repo.count_no_leidos(...)
```

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| **Mensajes entre usuarios de distintos tenants**: un usuario podría intentar enviar mensaje a un `destinatario_id` de otro tenant | `MensajeRepository.create` siempre asigna `tenant_id` desde el tenant del remitente. El service verifica que `destinatario_id` exista en el mismo tenant antes de crear el mensaje. |
| **Inbox grande**: un usuario con miles de mensajes podría tener lentitud en `GET /inbox` | La query de hilos agrupa por `hilo_id` y trae solo el último mensaje. Índice en `(tenant_id, destinatario_id, hilo_id)`. Paginación con offset/limit. |
| **hilo_id huérfano**: si un hilo se crea pero nunca se responde, queda un hilo de 1 mensaje | Es comportamiento esperado — un mensaje nuevo es un hilo de 1 mensaje. No necesita limpieza. |
| **CUIL como PII**: aunque readonly, el CUIL se expone en `GET /perfil` | El CUIL ya está cifrado en DB (AES-256). Se descifra al servirlo en el response (como ya hace `UserResponse`). No hay cambio de seguridad. |
| **Email duplicado en PUT /perfil**: el usuario podría cambiar su email a uno ya en uso | `UsuarioService.update_own_profile()` verifica unicidad de email en el mismo tenant antes de actualizar, igual que `update()` admin. |

## Migration Plan

1. **Nueva migración Alembic (1 archivo)**: (a) `ALTER TABLE users ADD COLUMN sexo VARCHAR(50) NULL`, (b) `CREATE TABLE mensajes (...)` con FK a `tenants` y `users`.
2. **Modelo `Mensaje`**: nuevo archivo `models/mensaje.py`.
3. **Campo `sexo` en `User`**: +1 columna en `models/user.py`.
4. **Schemas de perfil**: `PerfilUpdate`, `PerfilResponse` en `schemas/usuarios.py`.
5. **Schemas de mensajería**: nuevo módulo `schemas/mensajes.py`.
6. **Repositorio de mensajes**: nuevo archivo `repositories/mensaje_repository.py`.
7. **Servicio de mensajes**: nuevo archivo `services/mensaje_service.py`.
8. **Método en `UsuarioService`**: `update_own_profile()` con validación de readonly fields.
9. **Router de perfil**: nuevo archivo `routers/perfil.py`.
10. **Router de inbox**: nuevo archivo `routers/inbox.py`.
11. **Registro en `main.py`**: incluir ambos routers.
12. **Tests**: ~40 tests (perfil + mensajería).

**Rollback:** Revertir el commit y correr `alembic downgrade -1`.

## Open Questions

- *(ninguna — todas las decisiones están cerradas)*
