## Context

Este es el primer cambio frontend de activia-trace. El backend completo de autenticación y autorización (C-03, C-04) ya está implementado y operativo. Existen endpoints para login, 2FA, refresh con rotación, logout, recuperación y reseteo de contraseña.

No existe ninguna SPA aún. Todo el consumo actual es via API directa o testing. Este cambio crea el frontend desde cero: scaffolding, cliente HTTP, auth flow completo, layout y route guards.

**Stack decidido desde la arquitectura:**
- React 18 + TypeScript, Vite, TanStack Query, React Hook Form + Zod, Axios, Tailwind CSS.
- Feature-based modules: `features/{name}/{components,hooks,services,types,pages}`.
- Sin `any`, sin class components, componentes <200 LOC, pages lazy-loaded.

**Restricciones:**
- No modificar backend.
- Consumir endpoints existentes de C-03 (auth).
- El shell debe servir como base para C-22, C-23, C-24.

## Goals / Non-Goals

**Goals:**
- Scaffold completo del proyecto frontend con Vite + React 18 + TypeScript.
- Cliente Axios centralizado con interceptor de auth y refresh transparente con cola de requests concurrentes.
- Pantallas funcionales de login, 2FA, recuperación y reseteo de contraseña.
- AuthProvider con React Context que gestiona sesión, persistencia y refresh silencioso al montar.
- Route guard (`AuthGuard`) que redirige a `/login` sin sesión válida.
- `PermissionGuard` que verifica permisos antes de renderizar rutas protegidas (403 si no tiene permiso).
- AppLayout con sidebar dinámico (menú filtrado por permisos del usuario) y header con user info + logout.
- Shared UI components reutilizables: Button, Input, Card, Spinner, Alert.
- Tests de las piezas clave: render de login, flujo de auth mockeado, guard redirect, refresh transparente.
- Lazy loading de todas las páginas (React.lazy + Suspense).

**Non-Goals:**
- No implementar features de dominio (C-22, C-23, C-24). Solo el shell.
- No implementar diseño visual final (branding, colores corporativos). Tailwind base + tema neutro.
- No implementar server-side rendering (SSR) ni static generation — SPA pura.
- No implementar i18n. El MVP es en español.
- No implementar tema oscuro (se puede agregar después vía Tailwind class-based dark mode).
- No implementar tests E2E (Playwright) — solo unit + integration con Vitest + RTL.

## Architecture Decisions

### ADR-FE-001: React Router v6 Data Router (createBrowserRouter)

**Decisión**: Usar `createBrowserRouter` con layout routes en lugar de `<BrowserRouter>` tradicional.

**Racional**:
- `createBrowserRouter` es el patrón recomendado por React Router v6.4+.
- Permite layout routes anidadas: el AppLayout envuelve todas las rutas protegidas sin re-renderizar el layout.
- `errorElement` por ruta para manejo granular de errores.
- `loader`/`action` disponibles para data fetching futuro, pero en este cambio usamos TanStack Query para eso (los loaders se reservan para casos específicos de auth).

**Alternativa considerada**: `<BrowserRouter>` con `<Routes>` anidados. Funciona pero el data router es más declarativo y preparado para lazy loading.

### ADR-FE-002: Auth state en React Context + localStorage persist

**Decisión**: AuthProvider con React Context + persistencia selectiva en localStorage (refresh token solo).

**Racional**:
- El access token (15 min) se guarda en memoria (variable React state), no en localStorage — reduce superficie de ataque XSS.
- El refresh token se persiste en localStorage con clave `trace_refresh_token` para sobrevivir al refresh de página.
- El usuario autenticado (id, email, roles) se guarda en el context state. No se persiste — se refresca via `GET /api/v1/auth/me` al recargar la página.
- Los permisos se resuelven server-side en cada request (endpoints individuales con `require_permission`). El frontend cachea permisos en memoria para renderizar el menú, no para autorizar.

**Alternativa considerada**: Zustand para estado global. No se justifica para un solo slice de estado (auth). Si el estado global crece, se migra a Zustand en un cambio futuro.

### ADR-FE-003: Auth interceptor con cola de refresh (request queue)

**Decisión**: Implementar un `AuthInterceptor` con cola de requests concurrentes durante el refresh.

**Racional**:
- Cuando el access token expira, el interceptor de respuesta atrapa el 401.
- Antes de refrescar, establece un flag `isRefreshing = true`.
- Todos los requests que lleguen durante el refresh se encolan (Promise) y se resuelven cuando el refresh termina.
- Si el refresh falla, todos los requests encolados se rechazan y se redirige a `/login`.
- Esto evita N refresh simultáneos cuando N requests fallan 401 al mismo tiempo.

**Alternativa considerada**: Refrescar en cada request síncronamente. Ineficiente. Refrescar con setTimeout preventivo (antes de expirar). Más complejo y frágil; el enfoque reactivo con cola es más robusto.

### ADR-FE-004: Tailwind CSS v4 con @tailwindcss/vite plugin

**Decisión**: Usar Tailwind CSS v4 con el plugin nativo `@tailwindcss/vite`.

**Racional**:
- Tailwind v4 es la versión estable más reciente (2025/2026), con mejoras significativas de rendimiento y DX.
- El plugin `@tailwindcss/vite` elimina la necesidad de PostCSS + archivos de configuración separados (`tailwind.config.js`, `postcss.config.js`).
- Usa `@import "tailwindcss"` en el CSS en lugar de las directivas `@tailwind`.
- La configuración se hace con CSS-first config (variables CSS, `@theme`).

**Alternativa considerada**: Tailwind v3 con PostCSS. Más estable pero el plugin Vite nativo de v4 reduce la configuración y es el camino oficial.

### ADR-FE-005: Componentes UI atómicos con ref forwarding

**Decisión**: Cada componente UI compartido (Button, Input, Card, etc.) recibe `ref` via `forwardRef` y acepta className para extensión.

**Racional**:
- `react-hook-form` requiere `ref` en inputs para su sistema de registro.
- `className` permite a los consumers extender estilos sin violar encapsulamiento.
- Componentes puramente presentacionales: sin estado interno, sin lógica de negocio.

### ADR-FE-006: MSW (Mock Service Worker) para tests de integración HTTP

**Decisión**: Usar MSW v2 para interceptar requests HTTP en tests.

**Racional**:
- MSW intercepta en el nivel del `fetch`/`XMLHttpRequest`, no mockea Axios ni el módulo de servicios.
- Los tests son más fieles a la realidad: pasan por el interceptor de Axios real.
- Los handlers de MSW se reutilizan entre tests, organizados por feature.
- Elimina la necesidad de mockear Axios o el módulo `api.ts`.

**Alternativa considerada**: Mockear Axios con vitest-mock-extended. Más simple pero menos fiel. Los tests no validan el interceptor de refresh.

### ADR-FE-007: Layout y rutas con lazy loading

**Decisión**: React.lazy + Suspense para todas las páginas. El AppLayout carga sincrónicamente (es el shell).

**Racional**:
- Las páginas de login, 2FA, recuperación se cargan bajo demanda.
- El AppLayout (sidebar + header) se carga al inicio porque es el shell de la app.
- `Suspense` con fallback `<Spinner />` en cada grupo de rutas lazy.

## Component Tree

```
<App>
  <QueryClientProvider>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </QueryClientProvider>
</App>

Router (createBrowserRouter):
├── /login        → <LoginPage />          // pública
├── /2fa          → <TwoFactorPage />      // pública (requiere two_fa_token)
├── /recuperar    → <RecoveryPage />       // pública
├── /restablecer  → <ResetPasswordPage />  // pública
├── AuthLayout (AppLayout + AuthGuard)     // protegida
│   ├── /         → <DashboardRedirect />  // redirige a primer módulo según permisos
│   ├── /401      → <UnauthorizedPage />   // sin permiso
│   └── ... (C-22, C-23, C-24 agregan rutas aquí)
└── *             → <NotFoundPage />
```

## Data Flow — Auth

```
1. Login:
   LoginForm → authApi.login(email, password)
     ├── requires_2fa=false → AuthProvider.setSession(tokens, user)
     ├── requires_2fa=true → navigate("/2fa", { state: { twoFaToken } })
     └── error → mostrar error en formulario

2. 2FA:
   TwoFactorForm → authApi.verify2fa(twoFaToken, totpCode)
     ├── success → AuthProvider.setSession(tokens, user)
     └── error → mostrar error

3. Refresh silencioso (on mount):
   AuthProvider mount → localStorage.refresh_token existe?
     ├── sí → authApi.refresh(refreshToken)
     │   ├── success → AuthProvider.setSession(newTokens, user via /me)
     │   └── fail → limpiar todo, navigate("/login")
     └── no → navigate("/login")

4. Refresh en interceptor (durante 401):
   Axios response interceptor → error 401?
     ├── sí → encolar request, refrescar token
     │   ├── success → re-ejecutar request original con nuevo token
     │   └── fail → rechazar todos, AuthProvider.logout()
     └── no → propagar error

5. Logout:
   LogoutHandler → authApi.logout(refreshToken)
     → AuthProvider.clearSession()
     → navigate("/login")
```

## Route Design

```
/                     → Pública           → LoginPage
/login                → Pública           → LoginPage
/2fa                  → Pública           → TwoFactorPage
/recuperar            → Pública           → RecoveryPage
/restablecer          → Pública           → ResetPage
/* auth               → AuthGuard         → AppLayout
  /                   → DashboardRedirect
  /401                → UnauthorizedPage
  /*                  → NotFoundPage
```

## Directory Structure

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── src/
│   ├── main.tsx
│   ├── App.tsx                    # QueryClientProvider + AuthProvider + RouterProvider
│   ├── index.css                  # @import "tailwindcss"
│   ├── vite-env.d.ts
│   ├── shared/
│   │   ├── api/
│   │   │   └── api.ts             # Axios instance + interceptors
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Spinner.tsx
│   │   │   │   └── Alert.tsx
│   │   │   ├── layout/
│   │   │   │   └── AppLayout.tsx   # Sidebar + Header + Outlet
│   │   │   └── guards/
│   │   │       ├── AuthGuard.tsx
│   │   │       └── PermissionGuard.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── usePermissions.ts
│   │   └── providers/
│   │       └── AuthProvider.tsx
│   ├── features/
│   │   └── auth/
│   │       ├── components/
│   │       │   ├── LoginForm.tsx
│   │       │   ├── TwoFactorForm.tsx
│   │       │   ├── RecoveryForm.tsx
│   │       │   └── ResetPasswordForm.tsx
│   │       ├── hooks/
│   │       │   ├── useLogin.ts
│   │       │   ├── use2FA.ts
│   │       │   └── useRecovery.ts
│   │       ├── services/
│   │       │   └── authApi.ts
│   │       └── pages/
│   │           ├── LoginPage.tsx
│   │           ├── TwoFactorPage.tsx
│   │           ├── RecoveryPage.tsx
│   │           └── ResetPasswordPage.tsx
│   │       └── types/
│   │           └── index.ts
│   └── router/
│       └── index.tsx              # createBrowserRouter definition
├── vitest.config.ts (or in vite.config.ts)
└── tests/ or src/test/
    ├── setup.ts
    └── features/
        └── auth/
            ├── LoginPage.test.tsx
            ├── AuthGuard.test.tsx
            └── api.test.tsx
```

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| **Race condition en refresh**: múltiples requests fallan 401 simultáneamente y disparan N refreshes | Cola de concurrent requests: solo un refresh a la vez, los demás se encolan y re-ejecutan |
| **Refresh token robado**: localStorage vulnerable a XSS | El refresh token es de un solo uso (rotación). Si lo roban y lo usan, el legítimo falla y se fuerza relogin. Es el mismo modelo que el backend. El access token (15 min) nunca va a localStorage |
| **Versiones de Tailwind v4 inestables**: API aún cambiante | Pin exact version en package.json. Si hay breaking changes, se actualiza puntualmente |
| **MSW complejidad en CI**: puede dar falsos positivos si no se configura bien | Usar MSW en modo `setupServer` (node) para tests, no `setupWorker` (browser). Test helpers dedicados |
| **Crecimiento del context de Auth**: si se añaden demasiados datos, el provider se vuelve pesado | Mantener auth state mínimo: user, tokens, roles. Para datos pesados (permisos completos, preferencias), usar queries separadas con TanStack Query |
