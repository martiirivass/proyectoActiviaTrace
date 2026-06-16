import { get, post, patch, del } from '@/shared/api/api'
import type { Aviso, AvisoFormData, AckStats } from '@/features/coordinacion/types'

export const avisosService = {
  list: (): Promise<Aviso[]> =>
    get<Aviso[]>('/avisos'),

  getById: (id: string): Promise<Aviso> =>
    get<Aviso>(`/avisos/${id}`),

  create: (data: AvisoFormData): Promise<Aviso> =>
    post<Aviso>('/avisos', data),

  update: (id: string, data: Partial<AvisoFormData>): Promise<Aviso> =>
    patch<Aviso>(`/avisos/${id}`, data),

  delete: (id: string): Promise<void> =>
    del<void>(`/avisos/${id}`),

  getAckStats: (id: string): Promise<AckStats> =>
    get<AckStats>(`/avisos/${id}/ack-stats`),
}
