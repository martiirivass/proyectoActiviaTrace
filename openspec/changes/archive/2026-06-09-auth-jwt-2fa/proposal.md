## Why

C-02 estableció los modelos core (User, Tenant, Role) y el aislamiento multi-tenant. Sin autenticación, ninguna persona puede acceder al sistema. Se necesita un flujo completo de login con JWT, refresh con rotación, 2FA opcional y recuperación de contraseña — todo respetando la regla de oro: identidad exclusivamente desde la sesión verificada.

## What Changes

- `POST /api/auth/login` — email + password con Argon2id, emite par access (15 min) + refresh con rotación
- `POST /api/auth/refresh` — rota el refresh token, emite nuevo par; el viejo queda invalidado
- `POST /api/auth/logout` — revoca la sesión (invalida refresh)
- `POST /api/auth/2fa/enrol` — enrola TOTP para el usuario (genera secret, QR)
- `POST /api/auth/2fa/verify` — verifica código TOTP y completa el login
- `POST /api/auth/forgot` — genera token de un solo uso, lo envía al email del usuario
- `POST /api/auth/reset` — canjea token + nueva password; token queda invalidado
- Dependency `get_current_user` — resuelve identidad + tenant + roles desde el JWT verificado
- Rate limiting 5/60s por IP+email en login
- Claims mínimos en JWT: `sub` (user_id UUID), `tenant_id`, `roles`, `exp`

## Capabilities

### New Capabilities
- `user-auth`: Login con email+password (Argon2id), JWT access token (15 min), refresh token con rotación, logout con revocación, dependency `get_current_user` para proteger endpoints
- `two-factor-auth`: 2FA TOTP opcional por usuario — enrolar (secret + QR), verificar, gate entre login y emisión de sesión
- `rate-limiting`: Rate limit 5 intentos/60s por combinación IP+email en endpoint login, con almacenamiento en memoria

### Modified Capabilities
<!-- Ninguna — primera vez que se implementa auth -->

## Impact

- **backend/app/core/security.py** — Ampliar con generación/verificación JWT, refresh rotation, TOTP utils
- **backend/app/core/dependencies.py** — Nueva dependency `get_current_user` + `get_tenant`
- **backend/app/api/v1/routers/** — Nuevo router `auth.py` con todos los endpoints de auth
- **backend/app/schemas/** — Nuevos schemas Pydantic para requests/responses de auth
- **backend/app/services/** — Nuevo `auth_service.py` con lógica de login, refresh, 2FA, recovery
- **backend/app/repositories/** — Posible `session_repository.py` para refresh tokens
- **backend/app/models/** — Posible modelo `RefreshToken` (opcional, según diseño)
- **backend/app/core/config.py** — Nuevas settings: SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, etc.
- **Dependencias nuevas**: `python-jose[cryptography]` (JWT), `pyotp` (TOTP), `qrcode[pil]` (QR)
- **Rate limiting**: Implementación en memoria o vía dependency
