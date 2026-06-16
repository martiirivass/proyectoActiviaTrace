import { get, post, patch } from '@/shared/api/api'
import type { Tarea, TareaComment, TareaCreateRequest, TareaDelegarRequest, TareaEstadoChange, TareaCommentRequest, TareasFiltros } from '@/features/coordinacion/types'

export const tareasService = {
  list: (filtros?: TareasFiltros): Promise<Tarea[]> =>
    get<Tarea[]>('/tareas', { params: filtros }),

  getMisTareas: (): Promise<Tarea[]> =>
    get<Tarea[]>('/tareas/mias'),

  getById: (id: string): Promise<Tarea> =>
    get<Tarea>(`/tareas/${id}`),

  create: (data: TareaCreateRequest): Promise<Tarea> =>
    post<Tarea>('/tareas', data),

  cambiarEstado: (id: string, data: TareaEstadoChange): Promise<Tarea> =>
    patch<Tarea>(`/tareas/${id}/estado`, data),

  delegar: (data: TareaDelegarRequest): Promise<Tarea> =>
    post<Tarea>('/tareas/delegar', data),

  getComentarios: (tareaId: string): Promise<TareaComment[]> =>
    get<TareaComment[]>(`/tareas/${tareaId}/comentarios`),

  agregarComentario: (data: TareaCommentRequest): Promise<TareaComment> =>
    post<TareaComment>('/tareas/comentarios', data),
}
