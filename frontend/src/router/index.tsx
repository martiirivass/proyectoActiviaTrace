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

// Lazy-loaded pages - academico (C-22)
const DocenteDashboardPage = lazy(
  () => import('@/features/academico/pages/DocenteDashboardPage'),
)
const ComisionLayoutPage = lazy(
  () => import('@/features/academico/pages/ComisionLayoutPage'),
)
const CalificacionesPage = lazy(
  () => import('@/features/academico/pages/CalificacionesPage'),
)
const UmbralPage = lazy(() => import('@/features/academico/pages/UmbralPage'))
const AtrasadosPage = lazy(
  () => import('@/features/academico/pages/AtrasadosPage'),
)
const RankingPage = lazy(
  () => import('@/features/academico/pages/RankingPage'),
)
const NotasFinalesPage = lazy(
  () => import('@/features/academico/pages/NotasFinalesPage'),
)
const ReportesPage = lazy(
  () => import('@/features/academico/pages/ReportesPage'),
)
const ComunicacionesPage = lazy(
  () => import('@/features/academico/pages/ComunicacionesPage'),
)
const MonitorPage = lazy(
  () => import('@/features/academico/pages/MonitorPage'),
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
                <DocenteDashboardPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'comision/:materiaId/:cohorteId',
            element: (
              <SuspenseWrapper>
                <ComisionLayoutPage />
              </SuspenseWrapper>
            ),
            children: [
              {
                index: true,
                element: <Navigate to="calificaciones" replace />,
              },
              {
                path: 'calificaciones',
                element: (
                  <SuspenseWrapper>
                    <CalificacionesPage />
                  </SuspenseWrapper>
                ),
              },
              {
                path: 'umbral',
                element: (
                  <SuspenseWrapper>
                    <UmbralPage />
                  </SuspenseWrapper>
                ),
              },
              {
                path: 'atrasados',
                element: (
                  <SuspenseWrapper>
                    <AtrasadosPage />
                  </SuspenseWrapper>
                ),
              },
              {
                path: 'ranking',
                element: (
                  <SuspenseWrapper>
                    <RankingPage />
                  </SuspenseWrapper>
                ),
              },
              {
                path: 'notas',
                element: (
                  <SuspenseWrapper>
                    <NotasFinalesPage />
                  </SuspenseWrapper>
                ),
              },
              {
                path: 'reportes',
                element: (
                  <SuspenseWrapper>
                    <ReportesPage />
                  </SuspenseWrapper>
                ),
              },
              {
                path: 'comunicaciones',
                element: (
                  <SuspenseWrapper>
                    <ComunicacionesPage />
                  </SuspenseWrapper>
                ),
              },
            ],
          },
          {
            path: 'monitor',
            element: (
              <SuspenseWrapper>
                <MonitorPage />
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
