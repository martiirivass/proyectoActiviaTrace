## Why

activia-trace necesita una interfaz de usuario moderna, modular y segura para que los actores del sistema (PROFESOR, COORDINADOR, ADMIN, FINANZAS, etc.) puedan operar sobre los casos de uso ya implementados en el backend. Hasta ahora, todo el backend está construido (auth, RBAC, calificaciones, comunicaciones, etc.) pero no existe una SPA que consuma esos endpoints. Este cambio sienta las bases del frontend: el shell que todas las features posteriores (C-22, C-23, C-24) van a compartir.

## What Changes

1. **Scaffolding completo** de React 18 + TypeScript + Vite con estructura feature-based.
2. **Cliente HTTP centralizado** (Axios) con interceptor de auth y refresh transparente de tokens con cola de reintentos concurrentes para evitar múltiples refresh simultáneos.
3. **Pantallas de autenticación**:
   - `/login` — formulario de email + contraseña. Consume `POST /api/v1/auth/login`.
   - `/2fa` — verificación TOTP cuando el login responde con `requires_2fa: true`. Consume `POST /api/v1/auth/2fa/verify`.
   - `/recuperar` — solicitud de recuperación de contraseña. Consume `POST /api/v1/auth/forgot`.
   - `/restablecer` — establecimiento de nueva contraseña con token. Consume `POST /api/v1/auth/reset`.
4. **AuthProvider** con React Context: almacena usuario autenticado, permisos y tokens. En el mount, intenta refresh silencioso si hay refresh token almacenado.
5. **Route guard** (`AuthGuard` + `PermissionGuard`): protege rutas según sesión y permisos del usuario. Sin sesión → redirect a `/login`. Sin permiso → redirect a `/401` o mostrar mensaje.
6. **AppLayout** con sidebar/menú dinámico según permisos, header con info de usuario y botón de logout.
7. **Logout**: invalida el refresh token en backend (`POST /api/v1/auth/logout`) y limpia el estado local.
8. **Shared UI components**: Button, Input, Card, Spinner, Alert, HelpButton — base del sistema de diseño.
9. **Tests**: render de login, flujo de auth mockeado, guard redirect sin sesión, refresh transparente.

## Capabilities

### New Capabilities
- `auth-frontend`: Login, 2FA, password recovery/reset, logout, refresh token rotation — toda la capa de autenticación del frontend consumiendo los endpoints de C-03.
- `app-shell`: Layout principal (AppLayout, sidebar dinámico por permisos), AuthProvider, route guards (AuthGuard, PermissionGuard), shared UI components (Button, Input, Card, Spinner, Alert).
- `http-client`: Cliente Axios centralizado con interceptors de auth, refresh transparente con cola de concurrent requests, manejo de errores 401/403 estandarizado.

### Modified Capabilities
*(Ninguna — primer cambio frontend)*

## Impact

- **Nuevo directorio**: `frontend/` con scaffolding completo de Vite + React + TypeScript.
- **Dependencias nuevas** (package.json): react 18, react-dom, react-router-dom v6, @tanstack/react-query v5, axios, react-hook-form, @hookform/resolvers, zod, tailwindcss v4 (o v3 con postcss), @tailwindcss/vite, vitest, @testing-library/react, @testing-library/jest-dom, msw, jsdom.
- **Sin impacto en backend**: solo consume endpoints existentes de C-03. No modifica backend.
- **Sin impacto en features existentes** (C-22/23/24): este cambio es el prerequisito de todas ellas.
