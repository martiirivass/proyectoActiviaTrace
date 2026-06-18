import { get, post, put, del } from '@/shared/api/api'
import type { Usuario, UsuarioFormData, UsuarioFiltros, PaginatedResponse } from '@/features/admin/types'

export const usuariosService = {
  listar: (filtros?: UsuarioFiltros): Promise<PaginatedResponse<Usuario>> =>
    get<PaginatedResponse<Usuario>>('/admin/usuarios', { params: filtros }),

  getById: (id: string): Promise<Usuario> =>
    get<Usuario>(`/admin/usuarios/${id}`),

  create: (data: UsuarioFormData): Promise<Usuario> =>
    post<Usuario>('/admin/usuarios', data),

  update: (id: string, data: Partial<UsuarioFormData>): Promise<Usuario> =>
    put<Usuario>(`/admin/usuarios/${id}`, data),

  delete: (id: string): Promise<void> =>
    del<void>(`/admin/usuarios/${id}`),
}
