import { get, post, patch, del } from '@/shared/api/api'
import type { ColoquioMetrics, Convocatoria, ConvocatoriaFormData } from '@/features/coordinacion/types'

export const coloquiosService = {
  getMetrics: (): Promise<ColoquioMetrics> =>
    get<ColoquioMetrics>('/coloquios/metrics'),

  listConvocatorias: (): Promise<Convocatoria[]> =>
    get<Convocatoria[]>('/coloquios/convocatorias'),

  getConvocatoria: (id: string): Promise<Convocatoria> =>
    get<Convocatoria>(`/coloquios/convocatorias/${id}`),

  createConvocatoria: (data: ConvocatoriaFormData): Promise<Convocatoria> =>
    post<Convocatoria>('/coloquios/convocatorias', data),

  updateConvocatoria: (id: string, data: Partial<ConvocatoriaFormData>): Promise<Convocatoria> =>
    patch<Convocatoria>(`/coloquios/convocatorias/${id}`, data),

  deleteConvocatoria: (id: string): Promise<void> =>
    del<void>(`/coloquios/convocatorias/${id}`),
}
