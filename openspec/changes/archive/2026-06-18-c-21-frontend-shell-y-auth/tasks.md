## 1. Scaffolding — Vite + React 18 + TypeScript + Tailwind

- [x] 1.1 Scaffold project with `npm create vite@latest` (React + TypeScript template)
- [x] 1.2 Configure TypeScript: `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` con paths alias `@/*` → `./src/*`
- [x] 1.3 Install core dependencies: react-router-dom, @tanstack/react-query, axios, react-hook-form, @hookform/resolvers, zod
- [x] 1.4 Install Tailwind CSS v4 + `@tailwindcss/vite` plugin
- [x] 1.5 Install dev dependencies: vitest, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, msw, jsdom, @types/react, @types/react-dom
- [x] 1.6 Configure `vite.config.ts` with `@/` path alias, `@tailwindcss/vite` plugin, and vitest config
- [x] 1.7 Create `src/index.css` with `@import "tailwindcss"` directive
- [x] 1.8 Set up `src/vite-env.d.ts` with Vite client types and env types (`VITE_API_BASE_URL`)
- [x] 1.9 Create `.env.development` with `VITE_API_BASE_URL=http://localhost:8000/api/v1`
- [x] 1.10 Create feature-based directory structure: `features/auth/`, `shared/api/`, `shared/components/ui/`, `shared/components/layout/`, `shared/components/guards/`, `shared/hooks/`, `shared/providers/`, `router/`

## 2. Cliente HTTP centralizado (Axios + interceptors)

- [x] 2.1 Create `shared/api/api.ts`: Axios instance with baseURL from env, `Content-Type: application/json`, 30s timeout
- [x] 2.2 Implement request interceptor: attach `Authorization: Bearer <token>` from in-memory store
- [x] 2.3 Implement response interceptor: on 401, queue concurrent requests, attempt refresh via `POST /api/v1/auth/refresh`
- [x] 2.4 Handle refresh success: update stored tokens, retry all queued requests with new access token
- [x] 2.5 Handle refresh failure: clear tokens, reject all queued requests, redirect to `/login`
- [x] 2.6 On 403: reject with typed error for permission handling
- [x] 2.7 Export typed helper methods: `api.get<T>()`, `api.post<T>()`, `api.put<T>()`, `api.patch<T>()`, `api.delete<T>()`

## 3. AuthProvider con React Context

- [x] 3.1 Create `AuthContext` with `AuthContextType`: user, isAuthenticated, isLoading, login, logout, getAccessToken, permissions
- [x] 3.2 Create `AuthProvider` component: manages auth state, stores refresh token in localStorage, access token in memory
- [x] 3.3 Implement `loadSession` on mount: check for stored refresh token → attempt silent refresh → fetch `/me` → set user
- [x] 3.4 Implement `login(tokens)`: store access token in memory, refresh token in localStorage, fetch `/me` → set user
- [x] 3.5 Implement `logout()`: call `POST /api/v1/auth/logout`, clear all state, clear localStorage, redirect to `/login`
- [x] 3.6 Expose `useAuth()` hook with `AuthContextType`
- [x] 3.7 Expose `usePermissions()` hook that checks if user has specific permissions

## 4. Shared UI Components

- [x] 4.1 Create `Button.tsx`: forwardRef, variants (primary, secondary, danger), sizes (sm, md, lg), loading state with spinner, disabled state
- [x] 4.2 Create `Input.tsx`: forwardRef, label, error message, variants, className prop
- [x] 4.3 Create `Card.tsx`: container with shadow, optional header/body/footer sections
- [x] 4.4 Create `Spinner.tsx`: animated spinner with configurable size
- [x] 4.5 Create `Alert.tsx`: types (error, success, warning, info), optional dismiss button

## 5. Feature Auth — Servicios y hooks

- [x] 5.1 Create `features/auth/types/index.ts`: `LoginRequest`, `LoginResponse`, `TwoFAVerifyRequest`, `TwoFAVerifyResponse`, `RefreshRequest`, `RefreshResponse`, `ForgotRequest`, `ResetRequest`, `UserProfile`
- [x] 5.2 Create `features/auth/services/authApi.ts`:
  - `authApi.login(email, password)`: POST /auth/login → LoginResponse
  - `authApi.verify2fa(twoFaToken, code)`: POST /auth/2fa/verify → LoginResponse
  - `authApi.refresh(refreshToken)`: POST /auth/refresh → RefreshResponse
  - `authApi.logout(refreshToken)`: POST /auth/logout → void
  - `authApi.forgot(email)`: POST /auth/forgot → void
  - `authApi.reset(token, newPassword)`: POST /auth/reset → void
  - `authApi.me()`: GET /auth/me → UserProfile
- [x] 5.3 Create `features/auth/hooks/useLogin.ts`: handles form submission, calls authApi.login, navigates based on requires_2fa
- [x] 5.4 Create `features/auth/hooks/use2FA.ts`: handles TOTP submission, calls authApi.verify2fa
- [x] 5.5 Create `features/auth/hooks/useRecovery.ts`: handles forgot/reset flows

## 6. Feature Auth — Componentes y páginas

- [x] 6.1 Create `LoginForm.tsx`: React Hook Form + Zod validation (email required, password required, min 8 chars), submit via useLogin, error display via Alert
- [x] 6.2 Create `LoginPage.tsx`: renders LoginForm in a Card, lazy-loaded, <200 LOC, loading + error states
- [x] 6.3 Create `TwoFactorForm.tsx`: 6-digit TOTP input with React Hook Form + Zod, submit via use2FA
- [x] 6.4 Create `TwoFactorPage.tsx`: renders TwoFactorForm, accesses two_fa_token from router state, lazy-loaded
- [x] 6.5 Create `RecoveryForm.tsx`: email input, submit via useRecovery, shows success message
- [x] 6.6 Create `RecoveryPage.tsx`: renders RecoveryForm, lazy-loaded
- [x] 6.7 Create `ResetPasswordForm.tsx`: new password + confirm password fields, reads token from URL query param, submit via useRecovery
- [x] 6.8 Create `ResetPasswordPage.tsx`: renders ResetPasswordForm, lazy-loaded

## 7. Route guards y layout

- [x] 7.1 Create `AuthGuard.tsx`: checks `useAuth().isAuthenticated`, if false redirects to `/login` with `?redirect=` param
- [x] 7.2 Create `PermissionGuard.tsx`: accepts `requiredPermission` prop, checks via `usePermissions()`, if lacking shows unauthorized state
- [x] 7.3 Create `AppLayout.tsx`: sidebar with dynamic menu items based on user permissions, header with user info + logout, `<Outlet />` for nested routes, responsive (collapsible on mobile)
- [x] 7.4 Create `router/index.tsx`: `createBrowserRouter` with public routes (`/login`, `/2fa`, `/recuperar`, `/restablecer`), protected routes under AuthLayout, `errorElement` for 404, lazy imports for all pages

## 8. App bootstrap

- [x] 8.1 Create `App.tsx`: wraps app with `QueryClientProvider` + `AuthProvider` + `RouterProvider`
- [x] 8.2 Update `main.tsx`: imports `App.tsx`, renders into `#root` with StrictMode
- [x] 8.3 Update `index.html` with proper title "activia-trace" and meta tags

## 9. Tests

- [x] 9.1 Configure `src/test/setup.ts`: import `@testing-library/jest-dom`, configure MSW server with handlers
- [x] 9.2 Create test helpers: `renderWithProviders(ui, options)` wrapping component with AuthProvider + QueryClientProvider + MemoryRouter
- [x] 9.3 Create MSW handlers for auth endpoints: `/auth/login`, `/auth/2fa/verify`, `/auth/refresh`, `/auth/logout`
- [x] 9.4 Write `LoginPage.test.tsx`:
  - Renders login form
  - Shows validation errors on empty submit
  - Calls login API on valid submit
  - Displays server error on bad credentials
  - Redirects to 2FA when requires_2fa is true
- [x] 9.5 Write `AuthGuard.test.tsx`:
  - Redirects to /login when not authenticated
  - Renders children when authenticated
- [x] 9.6 Write `api.test.tsx`:
  - Attaches auth header when token exists
  - Transparent refresh on 401
  - Logs out on failed refresh
