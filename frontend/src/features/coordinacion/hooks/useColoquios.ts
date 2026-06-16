import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { coloquiosService } from '@/features/coordinacion/services/coloquiosService'
import type { ConvocatoriaFormData } from '@/features/coordinacion/types'

export function useColoquioMetrics() {
  return useQuery({
    queryKey: ['coloquios', 'metrics'],
    queryFn: () => coloquiosService.getMetrics(),
  })
}

export function useConvocatorias() {
  return useQuery({
    queryKey: ['coloquios', 'convocatorias'],
    queryFn: () => coloquiosService.listConvocatorias(),
  })
}

export function useConvocatoria(id: string | undefined) {
  return useQuery({
    queryKey: ['coloquios', 'convocatorias', id],
    queryFn: () => coloquiosService.getConvocatoria(id!),
    enabled: !!id,
  })
}

export function useCreateConvocatoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: ConvocatoriaFormData) => coloquiosService.createConvocatoria(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coloquios', 'convocatorias'] })
      queryClient.invalidateQueries({ queryKey: ['coloquios', 'metrics'] })
    },
  })
}

export function useUpdateConvocatoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ConvocatoriaFormData> }) =>
      coloquiosService.updateConvocatoria(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coloquios', 'convocatorias'] })
    },
  })
}

export function useDeleteConvocatoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => coloquiosService.deleteConvocatoria(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coloquios', 'convocatorias'] })
      queryClient.invalidateQueries({ queryKey: ['coloquios', 'metrics'] })
    },
  })
}
