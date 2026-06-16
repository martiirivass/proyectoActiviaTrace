import { lazy, Suspense } from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AuthGuard } from '@/shared/components/guards/AuthGuard'
import { AppLayout } from '@/shared/components/layout/AppLayout'
import { Spinner } from '@/shared/components/ui/Spinner'

// Lazy-loaded pages - auth
const LoginPage = lazy(() => import('@/features/auth/pages/LoginPage'))
const TwoFactorPage = lazy(() => import('@/features/auth/pages/TwoFactorPage'))
const RecoveryPage = lazy(() => import('@/features/auth/pages/RecoveryPage'))
const ResetPasswordPage = lazy(() => import('@/features/auth/pages/ResetPasswordPage'))

// Lazy-loaded pages - coordinacion (C-23)
const EquiposDashboardPage = lazy(
  () => import('@/features/coordinacion/pages/EquiposDashboardPage'),
)
const AvisosPage = lazy(
  () => import('@/features/coordinacion/pages/AvisosPage'),
)
const AvisoFormPage = lazy(
  () => import('@/features/coordinacion/pages/AvisoFormPage'),
)
const TareasPage = lazy(
  () => import('@/features/coordinacion/pages/TareasPage'),
)
const MisTareasPage = lazy(
  () => import('@/features/coordinacion/pages/MisTareasPage'),
)
const TareaDetailPage = lazy(
  () => import('@/features/coordinacion/pages/TareaDetailPage'),
)
const NuevaTareaPage = lazy(
  () => import('@/features/coordinacion/pages/NuevaTareaPage'),
)
const MonitorGeneralPage = lazy(
  () => import('@/features/coordinacion/pages/MonitorGeneralPage'),
)
const MonitorCoordinacionPage = lazy(
  () => import('@/features/coordinacion/pages/MonitorCoordinacionPage'),
)
const EncuentrosAdminPage = lazy(
  () => import('@/features/coordinacion/pages/EncuentrosAdminPage'),
)
const ColoquiosPage = lazy(
  () => import('@/features/coordinacion/pages/ColoquiosPage'),
)
const ConvocatoriasListPage = lazy(
  () => import('@/features/coordinacion/pages/ConvocatoriasListPage'),
)
const ConvocatoriaFormPage = lazy(
  () => import('@/features/coordinacion/pages/ConvocatoriaFormPage'),
)
const AdminColoquiosPage = lazy(
  () => import('@/features/coordinacion/pages/AdminColoquiosPage'),
)
const SetupCuatrimestrePage = lazy(
  () => import('@/features/coordinacion/pages/SetupCuatrimestrePage'),
)

function SuspenseWrapper({ children }: { children: React.ReactNode }) {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-svh items-center justify-center">
          <Spinner size="lg" />
        </div>
      }
    >
      {children}
    </Suspense>
  )
}

export const router = createBrowserRouter([
  // Public routes
  {
    path: '/login',
    element: (
      <SuspenseWrapper>
        <LoginPage />
      </SuspenseWrapper>
    ),
  },
  {
    path: '/2fa',
    element: (
      <SuspenseWrapper>
        <TwoFactorPage />
      </SuspenseWrapper>
    ),
  },
  {
    path: '/recuperar',
    element: (
      <SuspenseWrapper>
        <RecoveryPage />
      </SuspenseWrapper>
    ),
  },
  {
    path: '/restablecer',
    element: (
      <SuspenseWrapper>
        <ResetPasswordPage />
      </SuspenseWrapper>
    ),
  },
  // Protected routes
  {
    path: '/',
    element: <AuthGuard />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            index: true,
            element: <Navigate to="/dashboard" replace />,
          },
          {
            path: 'dashboard',
            element: (
              <SuspenseWrapper>
                <DashboardPlaceholder />
              </SuspenseWrapper>
            ),
          },
          // Coordinacion routes (C-23)
          {
            path: 'dashboard/coordinacion/equipos',
            element: (
              <SuspenseWrapper>
                <EquiposDashboardPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/avisos',
            element: (
              <SuspenseWrapper>
                <AvisosPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/avisos/nuevo',
            element: (
              <SuspenseWrapper>
                <AvisoFormPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/avisos/:id/editar',
            element: (
              <SuspenseWrapper>
                <AvisoFormPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/tareas',
            element: (
              <SuspenseWrapper>
                <TareasPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/tareas/mias',
            element: (
              <SuspenseWrapper>
                <MisTareasPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/tareas/nueva',
            element: (
              <SuspenseWrapper>
                <NuevaTareaPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/tareas/:id',
            element: (
              <SuspenseWrapper>
                <TareaDetailPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/encuentros',
            element: (
              <SuspenseWrapper>
                <EncuentrosAdminPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/coloquios',
            element: (
              <SuspenseWrapper>
                <ColoquiosPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/coloquios/admin',
            element: (
              <SuspenseWrapper>
                <AdminColoquiosPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/coloquios/convocatorias',
            element: (
              <SuspenseWrapper>
                <ConvocatoriasListPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/coloquios/convocatorias/nueva',
            element: (
              <SuspenseWrapper>
                <ConvocatoriaFormPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/coloquios/convocatorias/:id/editar',
            element: (
              <SuspenseWrapper>
                <ConvocatoriaFormPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'dashboard/coordinacion/setup',
            element: (
              <SuspenseWrapper>
                <SetupCuatrimestrePage />
              </SuspenseWrapper>
            ),
          },
          // Monitor routes for coordinacion (C-23)
          {
            path: 'monitor/general',
            element: (
              <SuspenseWrapper>
                <MonitorGeneralPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'monitor/coordinacion',
            element: (
              <SuspenseWrapper>
                <MonitorCoordinacionPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: '401',
            element: (
              <SuspenseWrapper>
                <UnauthorizedPlaceholder />
              </SuspenseWrapper>
            ),
          },
        ],
      },
    ],
  },
  // Catch-all 404
  {
    path: '*',
    element: (
      <SuspenseWrapper>
        <NotFoundPlaceholder />
      </SuspenseWrapper>
    ),
  },
])

function DashboardPlaceholder() {
  return (
    <div className="flex min-h-64 items-center justify-center">
      <p className="text-gray-500">Dashboard — próximamente</p>
    </div>
  )
}

function UnauthorizedPlaceholder() {
  return (
    <div className="flex min-h-64 items-center justify-center">
      <p className="text-gray-500">
        No tienes permisos suficientes para acceder a esta sección.
      </p>
    </div>
  )
}

function NotFoundPlaceholder() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900">404</h1>
        <p className="mt-2 text-gray-600">Página no encontrada</p>
        <a href="/login" className="mt-4 inline-block text-blue-600 hover:text-blue-800">
          Volver al inicio
        </a>
      </div>
    </div>
  )
}
