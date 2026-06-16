import { get, post } from '@/shared/api/api'
import type { LiquidacionResponse, LiquidacionHistorialEntry, PaginatedResponse } from '@/features/finanzas/types'

export const liquidacionesService = {
  listar: (cohorteId: string, periodo: string, kpis = true): Promise<LiquidacionResponse> =>
    get<LiquidacionResponse>('/liquidaciones', {
      params: { cohorte_id: cohorteId, periodo, kpis: kpis.toString() },
    }),

  calcular: (cohorteId: string, periodo: string): Promise<LiquidacionResponse> =>
    post<LiquidacionResponse>('/liquidaciones/calcular', null, {
      params: { cohorte_id: cohorteId, periodo },
    }),

  cerrar: (id: string): Promise<void> =>
    post<void>(`/liquidaciones/${id}/cerrar`),

  historial: (page = 1, perPage = 20): Promise<PaginatedResponse<LiquidacionHistorialEntry>> =>
    get<PaginatedResponse<LiquidacionHistorialEntry>>('/liquidaciones/historial', {
      params: { page, per_page: perPage },
    }),

  exportar: (cohorteId: string, periodo: string): Promise<Blob> =>
    get<Blob>('/liquidaciones/exportar', {
      params: { cohorte_id: cohorteId, periodo },
      responseType: 'blob',
    }),
}
