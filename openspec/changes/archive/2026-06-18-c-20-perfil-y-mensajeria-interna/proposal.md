## Why

Los usuarios del sistema (docentes, tutores, coordinadores, administradores) no tienen forma de editar su propio perfil — cada modificación de datos personales, bancarios o de contacto requiere intervención del ADMIN vía `usuarios:gestionar`. Esto es una fricción innecesaria para el usuario y una carga operativa para los administradores. Tampoco existe mensajería interna entre usuarios registrados: las únicas comunicaciones salientes son emails a alumnos (C-12). Los docentes no tienen un canal interno para notificaciones del sistema, avisos de coordinación o respuestas entre roles. Sin estas dos capacidades, el perfil del usuario es un registro estático y la colaboración entre roles depende de canales externos al sistema.

## What Changes

- **Nuevo endpoint `GET /api/v1/perfil`**: retorna el perfil completo del usuario autenticado (sin campos sensibles como `password_hash`, `totp_secret`).
- **Nuevo endpoint `PUT /api/v1/perfil`**: permite al usuario autenticado actualizar sus propios campos editables: `nombre`, `apellido`, `dni`, `sexo`, `cbu`, `alias_cbu`, `banco`, `regional`, `legajo_profesional`, `facturador`, `email`. Rechaza cambios a `cuil` o `legajo` con 422.
- **Nueva columna `sexo`** en tabla `users` (String(50), nullable) para soportar F11.1.
- **Nuevo modelo `Mensaje`** con tabla `mensajes`: mensajería interna entre usuarios registrados con agrupación por `hilo_id` (UUID compartido entre replies de un mismo hilo).
- **Nuevos endpoints** bajo `/api/v1/inbox`: `GET /inbox` (lista hilos), `GET /inbox/{hilo_id}` (mensajes de un hilo), `POST /inbox` (nuevo mensaje), `POST /inbox/{hilo_id}/responder` (responder en hilo).
- **Nueva migración Alembic**: agrega columna `sexo` a `users`, crea tabla `mensajes`.
- **No se requieren nuevos permisos**: perfil e inbox son accesibles por cualquier usuario autenticado. No se modifica la matriz RBAC existente.
- **No breaking**: los endpoints existentes de admin (C-07) para gestionar usuarios no se modifican. `GET /me` existente en auth no se modifica.

## Capabilities

### New Capabilities
- `profile-edit`: Edición del perfil propio por el usuario autenticado — lectura (`GET /perfil`) y actualización (`PUT /perfil`) con validación de campos editables vs. readonly.
- `internal-messaging`: Mensajería interna entre usuarios registrados — inbox con hilos, lectura de hilo, envío de nuevo mensaje, respuesta dentro de hilo, marcado de leído.

### Modified Capabilities
- *(ninguna — los specs existentes no cubren perfil ni mensajería)*

## Impact

- **Backend** (`models/user.py`): +1 columna `sexo`.
- **Backend** (`models/mensaje.py`): nuevo modelo `Mensaje` (~15 LOC).
- **Backend** (`schemas/usuarios.py`): +3 schemas (`PerfilUpdate`, `PerfilResponse`, `SexoEnum`).
- **Backend** (`schemas/mensajes.py`): nuevo módulo con schemas para inbox.
- **Backend** (`repositories/mensaje_repository.py`): nuevo repositorio con métodos de consulta de hilos.
- **Backend** (`repositories/usuario_repository.py`): +1 método `update_own_profile`.
- **Backend** (`services/mensaje_service.py`): nuevo servicio con lógica de envío/lectura.
- **Backend** (`services/usuario_service.py`): +1 método `update_own_profile` con validación de readonly fields.
- **Backend** (`routers/perfil.py`): nuevo router.
- **Backend** (`routers/inbox.py`): nuevo router.
- **Backend** (`main.py`): registro de 2 nuevos routers.
- **Backend** (migración Alembic): nueva migración para `sexo` + `mensajes`.
- **Tests**: ~40 tests nuevos (perfil + mensajería).
- **Dependencias**: C-07 (usuarios-y-asignaciones) completado — usuarios y repositorio base existen.
