import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usuariosService } from '@/features/admin/services/usuariosService'
import type { UsuarioFormData, UsuarioFiltros } from '@/features/admin/types'

export function useUsuarios(filtros?: UsuarioFiltros) {
  return useQuery({
    queryKey: ['usuarios', filtros],
    queryFn: () => usuariosService.listar(filtros),
  })
}

export function useUsuario(id: string) {
  return useQuery({
    queryKey: ['usuario', id],
    queryFn: () => usuariosService.getById(id),
    enabled: !!id,
  })
}

export function useCreateUsuario() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: UsuarioFormData) => usuariosService.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['usuarios'] }),
  })
}

export function useUpdateUsuario() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<UsuarioFormData> }) =>
      usuariosService.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['usuarios'] }),
  })
}

export function useDeleteUsuario() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => usuariosService.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['usuarios'] }),
  })
}
