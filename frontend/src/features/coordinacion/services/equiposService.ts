import { get, post, patch } from '@/shared/api/api'
import type { EquipoAssignment, MisEquiposFiltros, AsignacionesFiltros, AsignacionMasivaRequest, ClonarEquipoRequest, VigenciaEquipoRequest } from '@/features/coordinacion/types'

export const equiposService = {
  getMisEquipos: (filtros?: MisEquiposFiltros): Promise<EquipoAssignment[]> =>
    get<EquipoAssignment[]>('/equipos/mis-equipos', { params: filtros }),

  getAsignaciones: (filtros?: AsignacionesFiltros): Promise<EquipoAssignment[]> =>
    get<EquipoAssignment[]>('/equipos/asignaciones', { params: filtros }),

  asignacionMasiva: (data: AsignacionMasivaRequest): Promise<EquipoAssignment[]> =>
    post<EquipoAssignment[]>('/equipos/asignacion-masiva', data),

  clonarEquipo: (data: ClonarEquipoRequest): Promise<EquipoAssignment[]> =>
    post<EquipoAssignment[]>('/equipos/clonar', data),

  modificarVigencia: (data: VigenciaEquipoRequest): Promise<EquipoAssignment[]> =>
    patch<EquipoAssignment[]>('/equipos/vigencia', data),

  exportar: (materiaId: string, carreraId: string, cohorteId: string): Promise<Blob> =>
    get<Blob>('/equipos/exportar', {
      params: { materia_id: materiaId, carrera_id: carreraId, cohorte_id: cohorteId },
      responseType: 'blob',
    }),
}
