import { get, post } from '@/shared/api/api'
import type {
  ComunicacionPreview,
  ComunicacionPreviewRequest,
  EnviarComunicacionRequest,
  EnviarComunicacionResponse,
  TrackingLote,
  SeguimientoMateria,
} from '@/features/academico/types'

export const comunicacionesService = {
  preview: (data: ComunicacionPreviewRequest): Promise<ComunicacionPreview> =>
    post<ComunicacionPreview>('/comunicaciones/preview', data),

  enviarIndividual: (data: EnviarComunicacionRequest): Promise<EnviarComunicacionResponse> =>
    post<EnviarComunicacionResponse>('/comunicaciones/enviar', data),

  enviarLote: (data: EnviarComunicacionRequest): Promise<EnviarComunicacionResponse> =>
    post<EnviarComunicacionResponse>('/comunicaciones/enviar-lote', data),

  getTrackingPorLote: (loteId: string): Promise<TrackingLote> =>
    get<TrackingLote>(`/comunicaciones/lote/${loteId}`),

  getTrackingPorMateria: (materiaId: string): Promise<SeguimientoMateria> =>
    get<SeguimientoMateria>(`/comunicaciones/materia/${materiaId}`),
}
