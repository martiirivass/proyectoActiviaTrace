import { describe, it, expect } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders, mockUser } from '@/test/test-utils'
import { AuditoriaDashboardView } from '@/features/admin/components/AuditoriaDashboardView'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthContext } from '@/shared/providers/AuthProvider'

function renderWithAuth() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return renderWithProviders(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={{
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        permissions: ['auditoria:read'],
        login: async () => {},
        logout: async () => {},
        getAccessToken: () => 'mock-token',
      }}>
        <AuditoriaDashboardView />
      </AuthContext.Provider>
    </QueryClientProvider>,
  )
}

describe('AuditDashboard', () => {
  it('renders all 4 dashboard sections', async () => {
    renderWithAuth()

    await waitFor(() => {
      expect(screen.getByText('Panel de Auditoría')).toBeInTheDocument()
      expect(screen.getByText('Total Comunicaciones')).toBeInTheDocument()
      expect(screen.getByText('Interacciones D/M')).toBeInTheDocument()
    })
  })

  it('shows chart section', async () => {
    renderWithAuth()

    await waitFor(() => {
      expect(screen.getByText('Acciones por Día')).toBeInTheDocument()
    })
  })

  it('shows comunicaciones por docente table', async () => {
    renderWithAuth()

    await waitFor(() => {
      expect(screen.getByText('Comunicaciones por Docente')).toBeInTheDocument()
      const items = screen.getAllByText('Juan Pérez')
      expect(items.length).toBeGreaterThanOrEqual(1)
    })
  })

  it('shows ultimas acciones table', async () => {
    renderWithAuth()

    await waitFor(() => {
      const elements = screen.getAllByText('Últimas Acciones')
      expect(elements.length).toBeGreaterThanOrEqual(1)
    })
  })

  it('filters by date range', async () => {
    renderWithAuth()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByLabelText('Desde')).toBeInTheDocument()
      expect(screen.getByLabelText('Hasta')).toBeInTheDocument()
    })

    const desdeInput = screen.getByLabelText('Desde')
    await user.type(desdeInput, '2026-06-01')

    const hastaInput = screen.getByLabelText('Hasta')
    await user.type(hastaInput, '2026-06-30')

    await user.click(screen.getByText('Filtrar'))

    await waitFor(() => {
      const elements = screen.getAllByText('Total Comunicaciones')
      expect(elements.length).toBeGreaterThanOrEqual(1)
    })
  })
})
