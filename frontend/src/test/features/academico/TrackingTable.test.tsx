import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, render, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TrackingTable } from '@/features/academico/components/TrackingTable'

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/comision/mat-1/coh-1/comunicaciones']}>
        <Routes>
          <Route path="/comision/:materiaId/:cohorteId/comunicaciones" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('TrackingTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows distribution summary', async () => {
    renderWithProviders(<TrackingTable />)

    await waitFor(() => {
      expect(screen.getByText(/Pendientes/)).toBeInTheDocument()
    })
    expect(screen.getByText(/Enviados/)).toBeInTheDocument()
    expect(screen.getByText(/Enviando/)).toBeInTheDocument()
  })

  it('displays correct estado badges', async () => {
    renderWithProviders(<TrackingTable />)

    await waitFor(() => {
      expect(screen.getAllByText(/Enviado/).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/Pendiente/).length).toBeGreaterThan(0)
    })
  })

  it('shows table with communications', async () => {
    renderWithProviders(<TrackingTable />)

    await waitFor(() => {
      expect(screen.getByText(/Aviso importante/)).toBeInTheDocument()
      expect(screen.getByText(/Recordatorio/)).toBeInTheDocument()
    })
  })
})
