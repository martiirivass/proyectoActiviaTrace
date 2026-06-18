import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tareasService } from '@/features/coordinacion/services/tareasService'
import type { TareasFiltros, TareaCreateRequest, TareaEstadoChange, TareaDelegarRequest, TareaCommentRequest } from '@/features/coordinacion/types'

export function useTareas(filtros?: TareasFiltros) {
  return useQuery({
    queryKey: ['tareas', filtros],
    queryFn: () => tareasService.list(filtros),
  })
}

export function useMisTareas() {
  return useQuery({
    queryKey: ['tareas', 'mias'],
    queryFn: () => tareasService.getMisTareas(),
  })
}

export function useTarea(id: string | undefined) {
  return useQuery({
    queryKey: ['tareas', id],
    queryFn: () => tareasService.getById(id!),
    enabled: !!id,
  })
}

export function useCreateTarea() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: TareaCreateRequest) => tareasService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tareas'] })
    },
  })
}

export function useCambiarEstadoTarea() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TareaEstadoChange }) =>
      tareasService.cambiarEstado(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tareas'] })
    },
  })
}

export function useDelegarTarea() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: TareaDelegarRequest) => tareasService.delegar(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tareas'] })
    },
  })
}

export function useComentariosTarea(tareaId: string | undefined) {
  return useQuery({
    queryKey: ['tareas', tareaId, 'comentarios'],
    queryFn: () => tareasService.getComentarios(tareaId!),
    enabled: !!tareaId,
  })
}

export function useAgregarComentario() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: TareaCommentRequest) => tareasService.agregarComentario(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['tareas', variables.tarea_id, 'comentarios'],
      })
    },
  })
}
