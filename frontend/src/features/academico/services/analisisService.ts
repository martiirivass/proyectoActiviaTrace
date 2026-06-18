import { get } from '@/shared/api/api'
import type { AtrasadoEntry, RankingEntry, NotaFinalEntry, ReporteRapido } from '@/features/academico/types'

export const analisisService = {
  getAtrasados: (materiaId: string, busqueda?: string): Promise<AtrasadoEntry[]> =>
    get<AtrasadoEntry[]>('/analisis/atrasados', {
      params: { materia_id: materiaId, ...(busqueda ? { busqueda } : {}) },
    }),

  getRanking: (materiaId: string): Promise<RankingEntry[]> =>
    get<RankingEntry[]>('/analisis/ranking', { params: { materia_id: materiaId } }),

  getNotasFinales: (materiaId: string): Promise<NotaFinalEntry[]> =>
    get<NotaFinalEntry[]>('/notas-finales', { params: { materia_id: materiaId } }),

  getReportes: (materiaId: string): Promise<ReporteRapido> =>
    get<ReporteRapido>('/analisis/reportes-rapidos', { params: { materia_id: materiaId } }),

  exportarTPs: (materiaId: string): Promise<Blob> =>
    get<Blob>('/analisis/exportar-tps', {
      params: { materia_id: materiaId },
      responseType: 'blob',
    }),
}
