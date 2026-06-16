import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { avisosService } from '@/features/coordinacion/services/avisosService'
import type { AvisoFormData } from '@/features/coordinacion/types'

export function useAvisos() {
  return useQuery({
    queryKey: ['avisos'],
    queryFn: () => avisosService.list(),
  })
}

export function useAviso(id: string | undefined) {
  return useQuery({
    queryKey: ['avisos', id],
    queryFn: () => avisosService.getById(id!),
    enabled: !!id,
  })
}

export function useCreateAviso() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: AvisoFormData) => avisosService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] })
    },
  })
}

export function useUpdateAviso() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<AvisoFormData> }) =>
      avisosService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] })
    },
  })
}

export function useDeleteAviso() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => avisosService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['avisos'] })
    },
  })
}

export function useAckStats(id: string | undefined) {
  return useQuery({
    queryKey: ['avisos', id, 'ack-stats'],
    queryFn: () => avisosService.getAckStats(id!),
    enabled: !!id,
  })
}
