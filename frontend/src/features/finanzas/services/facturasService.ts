import { get, post, put, del } from '@/shared/api/api'
import type { Factura, FacturaFormData, FacturaFiltros } from '@/features/finanzas/types'

export const facturasService = {
  listar: (filtros?: FacturaFiltros): Promise<Factura[]> =>
    get<Factura[]>('/facturas', { params: filtros }),

  getById: (id: string): Promise<Factura> =>
    get<Factura>(`/facturas/${id}`),

  create: (data: FacturaFormData): Promise<Factura> =>
    post<Factura>('/facturas', data),

  update: (id: string, data: Partial<FacturaFormData>): Promise<Factura> =>
    put<Factura>(`/facturas/${id}`, data),

  abonar: (id: string): Promise<Factura> =>
    post<Factura>(`/facturas/${id}/abonar`),

  delete: (id: string): Promise<void> =>
    del<void>(`/facturas/${id}`),
}
