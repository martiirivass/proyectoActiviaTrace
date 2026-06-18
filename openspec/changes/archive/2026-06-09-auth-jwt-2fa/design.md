## Context

C-02 implementó los modelos core (User, Tenant, Role, Permission, UserRole, UserTenant), el aislamiento multi-tenant via TenantScopedRepository, PasswordService con Argon2id y EncryptionService con AES-256-GCM. La app FastAPI ya tiene health-check, configuración Pydantic desde .env, conexión async a PostgreSQL y OpenTelemetry.

Ahora se necesita el flujo completo de autenticación: login con JWT, refresh rotation, 2FA opcional (TOTP), recuperación de contraseña y rate limiting. Todo respetando la regla de oro: identidad y tenant **exclusivamente desde la sesión verificada**.

## Goals / Non-Goals

**Goals:**
- Login con email + password (Argon2id) que emite par JWT access + refresh
- Refresh rotation: cada uso del refresh invalida el anterior y emite uno nuevo
- Logout explícito que revoca la sesión
- 2FA TOTP opcional por usuario: enrolar (secret + QR) y verificar como gate antes de emitir sesión
- Recuperación de contraseña: forgot (token single-use por email) + reset
- Dependency `get_current_user` que resuelve user, tenant, roles desde el JWT
- Rate limiting 5 intentos/60s por IP+email en login
- Claims mínimos JWT: `sub` (user_id UUID), `tenant_id`, `roles`, `exp`, `type` (access/refresh)

**Non-Goals:**
- No se implementa RBAC fino (`require_permission`) — eso es C-04
- No se implementa impersonación — eso es C-05
- No se implementa frontend de login — eso es C-21
- No se implementa envío real de emails (forgot/reset) — solo generación de token
- No se implementa almacenamiento persistente de rate limiting (en memoria es suficiente para esta etapa)

## Decisions

### D1: JWT con refresh rotation (no opaque tokens)
- **Decisión**: Usar JWT access (15 min) + refresh token con rotación almacenado en DB
- **Por qué**: JWT permite validación stateless del access token (no requiere DB lookup en cada request). El refresh queda en DB para soportar revocación explícita y rotación (seguridad: si roban un refresh, al usarlo el legítimo dueño lo detecta porque su token queda invalidado).
- **Alternativa considerada**: Opaque tokens (todo en DB) — descartado porque requiere DB lookup en cada request, latencia adicional.
- **Alternativa considerada**: JWT sin refresh (solo access largo) — descartado porque 15 min es muy corto para sesiones de usuario, y access más largos son inseguros.

### D2: 2FA TOTP opcional por usuario
- **Decisión**: TOTP estándar (RFC 6238) con secret por usuario, enrolamiento genera QR para Google Authenticator/Authy
- **Por qué**: Estándar abierto, no depende de servicios externos, el usuario controla su segundo factor
- **Gate**: Entre validación de password y emisión de sesión; si 2FA está habilitado, login devuelve `2fa_required` en lugar de tokens

### D3: Refresh token almacenado en tabla `refresh_tokens`
- **Decisión**: Modelo `RefreshToken` con `id`, `user_id`, `token_hash` (SHA-256 del token), `expires_at`, `revoked_at`, `created_at`
- **Por qué**: Hash del token en DB (no texto plano), soporta revocación, rotación y listado de sesiones activas
- **Alternativa considerada**: Almacenar en Redis — descartado porque agrega dependencia de infraestructura; PostgreSQL es suficiente para el volumen esperado

### D4: Rate limiting en memoria
- **Decisión**: Diccionario en memoria con ventana deslizante por IP+email
- **Por qué**: Simple, no requiere Redis, suficiente para protección contra fuerza bruta. Se reinicia al reiniciar la app (aceptable para esta etapa)
- **Alternativa considerada**: Redis — descartado como dependencia adicional por ahora; se puede agregar después si es necesario

### D5: Password recovery con token single-use
- **Decisión**: Tabla `recovery_tokens` con `id`, `user_id`, `token_hash`, `expires_at`, `used_at`
- **Por qué**: Token de un solo uso con expiración corta (15 min), hash en DB
- **Nota**: El envío real del email se implementa en C-12 (comunicaciones) o como integración separada; este change solo genera el token y el endpoint de canje

## Risks / Trade-offs

- **[Rate limiting en memoria] → Se pierde al reiniciar la app.** Aceptable para MVP. Migrar a Redis si hay múltiples instancias o necesidad de persistencia.
- **[Refresh token en PostgreSQL] → Latencia en login/refresh.** El volumen esperado es bajo (cientos de usuarios, no millones). Si escala, migrar a Redis.
- **[JWT sin permisos en claims] → Cada request resuelve roles desde DB.** Trade-off intencional: los permisos son dinámicos (cambian con asignaciones), no deberían cachearse en token. La latencia de la DB lookup es despreciable comparada con la seguridad.
- **[2FA TOTP obliga a usuario tener dispositivo] → El 2FA es opcional por usuario.** Habilitado por decisión del usuario, no forzado por el sistema.
- **[Forgot/reset sin email real] → El endpoint genera el token pero no envía el email.** Se integra con C-12 o con el provider de emails cuando esté disponible. Mientras tanto, el token se devuelve en la respuesta para testing.
