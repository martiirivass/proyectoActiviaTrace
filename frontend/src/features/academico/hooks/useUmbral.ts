import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { umbralService } from '@/features/academico/services/umbralService'
import type { UpdateUmbralRequest } from '@/features/academico/types'

export function useUmbral(materiaId: string) {
  return useQuery({
    queryKey: ['umbral', materiaId],
    queryFn: () => umbralService.getUmbral(materiaId),
    enabled: !!materiaId,
  })
}

export function useUpdateUmbral() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateUmbralRequest) =>
      umbralService.updateUmbral(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['umbral', variables.materia_id] })
    },
  })
}

export function useRecalcularUmbral() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (materiaId: string) => umbralService.recalcular(materiaId),
    onSuccess: (_data, materiaId) => {
      queryClient.invalidateQueries({ queryKey: ['umbral', materiaId] })
      queryClient.invalidateQueries({ queryKey: ['atrasados'] })
      queryClient.invalidateQueries({ queryKey: ['ranking'] })
    },
  })
}
