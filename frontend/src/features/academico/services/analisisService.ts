import { get } from '@/shared/api/api'
import type { AtrasadoEntry, RankingEntry, NotaFinalEntry, ReporteRapido } from '@/features/academico/types'

export const analisisService = {
  getAtrasados: async (materiaId: string, busqueda?: string): Promise<AtrasadoEntry[]> => {
    const res = await get<{ items: any[]; total: number }>('/analisis/atrasados', {
      params: { materia_id: materiaId, ...(busqueda ? { busqueda } : {}) },
    })
    return res.items.map((item: any) => ({
      alumno: {
        id: item.alumno_id ?? '',
        legajo: '',
        nombre: item.alumno_nombre ?? '',
        apellido: item.alumno_apellido ?? '',
        email: item.email ?? '',
      },
      actividad: item.actividad,
      causa: item.causa,
    }))
  },

  getRanking: async (materiaId: string): Promise<RankingEntry[]> => {
    const res = await get<{ items: any[]; total: number }>('/analisis/ranking', {
      params: { materia_id: materiaId },
    })
    return res.items.map((item: any) => ({
      posicion: item.posicion ?? 0,
      alumno: {
        id: item.alumno_id ?? '',
        legajo: '',
        nombre: item.alumno_nombre ?? '',
        apellido: item.alumno_apellido ?? '',
        email: item.email ?? '',
      },
      email: item.email ?? '',
      comision: item.comision ?? '',
      aprobadas: item.aprobadas ?? 0,
      total: item.total ?? 0,
      porcentaje: item.porcentaje ?? 0,
    }))
  },

  getNotasFinales: async (materiaId: string): Promise<NotaFinalEntry[]> => {
    const res = await get<{ items: any[]; total: number }>('/analisis/notas-finales', {
      params: { materia_id: materiaId },
    })
    return res.items.map((item: any) => ({
      alumno: {
        id: item.alumno_id ?? '',
        legajo: '',
        nombre: item.alumno_nombre ?? '',
        apellido: item.alumno_apellido ?? '',
        email: item.email ?? '',
      },
      email: item.email ?? '',
      comision: item.comision ?? '',
      actividades_consideradas: item.actividades_consideradas ?? 0,
      nota_final: item.nota_final ?? null,
      actividades: (item.actividades ?? []).map((act: any) => ({
        nombre: act.nombre ?? '',
        nota: act.nota ?? null,
      })),
    }))
  },

  getReportes: (materiaId: string): Promise<ReporteRapido> =>
    get<ReporteRapido>('/analisis/reportes-rapidos', { params: { materia_id: materiaId } }),

  exportarTPs: (materiaId: string): Promise<Blob> =>
    get<Blob>('/analisis/exportar-tps-sin-corregir', {
      params: { materia_id: materiaId },
      responseType: 'blob',
    }),
}
