import { get, post } from '@/shared/api/api'
import type {
  ComunicacionPreview,
  ComunicacionPreviewRequest,
  EnviarComunicacionRequest,
  EnviarComunicacionResponse,
  TrackingLote,
  SeguimientoMateria,
  TrackingMessage,
  TrackingDistribucion,
} from '@/features/academico/types'

export const comunicacionesService = {
  preview: (data: ComunicacionPreviewRequest): Promise<ComunicacionPreview> =>
    post<ComunicacionPreview>('/comunicaciones/preview', data),

  enviarIndividual: (data: EnviarComunicacionRequest): Promise<EnviarComunicacionResponse> =>
    post<EnviarComunicacionResponse>('/comunicaciones/individual', {
      asunto: data.asunto,
      cuerpo: data.cuerpo,
      materia_id: data.materia_id,
      destinatario_email: data.destinatarios[0],
    }),

  enviarLote: (data: EnviarComunicacionRequest): Promise<EnviarComunicacionResponse> =>
    post<EnviarComunicacionResponse>('/comunicaciones/masivo', data),

  getTrackingPorLote: (loteId: string): Promise<TrackingLote> =>
    get<TrackingLote>(`/comunicaciones/lotes/${loteId}`),

  getTrackingPorMateria: async (materiaId: string): Promise<SeguimientoMateria> => {
    // GET /comunicaciones returns {items, total, offset, limit}
    const listRes = await get<{
      items: any[]
      total: number
      offset: number
      limit: number
    }>('/comunicaciones', { params: { materia_id: materiaId } })

    // GET /comunicaciones/distribucion returns DistribucionEstados
    const distribucion = await get<TrackingDistribucion>('/comunicaciones/distribucion', {
      params: { materia_id: materiaId },
    })

    const comunicaciones: TrackingMessage[] = listRes.items.map((item: any) => ({
      id: item.id ?? '',
      destinatario: item.destinatario ?? '',
      asunto: item.asunto ?? '',
      estado: item.estado ?? ('pendiente' as const),
      fecha_envio: item.enviado_at ?? item.created_at ?? null,
    }))

    return { comunicaciones, distribucion }
  },
}
