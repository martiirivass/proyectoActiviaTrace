import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { comunicacionesService } from '@/features/academico/services/comunicacionesService'
import type {
  ComunicacionPreviewRequest,
  EnviarComunicacionRequest,
} from '@/features/academico/types'

export function usePreviewComunicacion() {
  return useMutation({
    mutationFn: (data: ComunicacionPreviewRequest) =>
      comunicacionesService.preview(data),
  })
}

export function useEnviarIndividual() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: EnviarComunicacionRequest) =>
      comunicacionesService.enviarIndividual(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['comunicaciones-materia', variables.materia_id],
      })
    },
  })
}

export function useEnviarLote() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: EnviarComunicacionRequest) =>
      comunicacionesService.enviarLote(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['comunicaciones-materia', variables.materia_id],
      })
    },
  })
}

export function useTrackingPorLote(loteId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ['comunicaciones-lote', loteId],
    queryFn: () => comunicacionesService.getTrackingPorLote(loteId!),
    enabled: enabled && !!loteId,
    refetchInterval: (query) => {
      if (!query.state.data) return 5000
      const { distribucion } = query.state.data
      const active = distribucion.pendiente + distribucion.enviando
      return active > 0 ? 5000 : false
    },
  })
}

export function useTrackingPorMateria(materiaId: string) {
  return useQuery({
    queryKey: ['comunicaciones-materia', materiaId],
    queryFn: () => comunicacionesService.getTrackingPorMateria(materiaId),
    enabled: !!materiaId,
  })
}
