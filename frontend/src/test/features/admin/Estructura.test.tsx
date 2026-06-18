import { describe, it, expect } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders, mockUser } from '@/test/test-utils'
import { EstructuraView } from '@/features/admin/components/EstructuraView'
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
        permissions: ['estructura:gestionar'],
        login: async () => {},
        logout: async () => {},
        getAccessToken: () => 'mock-token',
      }}>
        <EstructuraView />
      </AuthContext.Provider>
    </QueryClientProvider>,
  )
}

describe('Estructura Académica', () => {
  it('renders tabs and loads carreras', async () => {
    renderWithAuth()

    expect(screen.getByText('Carreras')).toBeInTheDocument()
    expect(screen.getByText('Cohortes')).toBeInTheDocument()
    expect(screen.getByText('Materias')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('ING-INFO')).toBeInTheDocument()
      expect(screen.getByText('Ingeniería Informática')).toBeInTheDocument()
    })
  })

  it('switches to Cohortes tab', async () => {
    renderWithAuth()
    const user = userEvent.setup()

    await user.click(screen.getByText('Cohortes'))

    await waitFor(() => {
      expect(screen.getByText('Filtrar por ID Carrera')).toBeInTheDocument()
    })
  })

  it('switches to Materias tab and loads data', async () => {
    renderWithAuth()
    const user = userEvent.setup()

    await user.click(screen.getByText('Materias'))

    await waitFor(() => {
      expect(screen.getByText('MAT-101')).toBeInTheDocument()
      expect(screen.getByText('Matemática I')).toBeInTheDocument()
    })
  })

  it('creates a new carrera', async () => {
    renderWithAuth()
    const user = userEvent.setup()

    await waitFor(() => {
      expect(screen.getByText('Nueva Carrera')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Nueva Carrera'))

    await waitFor(() => {
      const headings = screen.getAllByText('Nueva Carrera')
      expect(headings.length).toBeGreaterThanOrEqual(2)
    })
  })
})
