import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, render, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AtrasadosTable } from '@/features/academico/components/AtrasadosTable'

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/comision/mat-1/coh-1/atrasados']}>
        <Routes>
          <Route path="/comision/:materiaId/:cohorteId/atrasados" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('AtrasadosTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders atrasados list', async () => {
    renderWithProviders(<AtrasadosTable />)

    await waitFor(() => {
      expect(screen.getByText(/Pérez/)).toBeInTheDocument()
    })
    expect(screen.getByText(/García/)).toBeInTheDocument()
  })

  it('displays correct cause badge', async () => {
    renderWithProviders(<AtrasadosTable />)

    await waitFor(() => {
      expect(screen.getByText(/Nota bajo umbral/)).toBeInTheDocument()
    })
    expect(screen.getByText(/Actividad faltante/)).toBeInTheDocument()
  })
})
