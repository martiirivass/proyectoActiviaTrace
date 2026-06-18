import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { liquidacionesService } from '@/features/finanzas/services/liquidacionesService'

export function useLiquidaciones(cohorteId: string, periodo: string) {
  return useQuery({
    queryKey: ['liquidaciones', cohorteId, periodo],
    queryFn: () => liquidacionesService.listar(cohorteId, periodo, true),
    enabled: !!cohorteId && !!periodo,
  })
}

export function useCalcularLiquidacion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ cohorteId, periodo }: { cohorteId: string; periodo: string }) =>
      liquidacionesService.calcular(cohorteId, periodo),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['liquidaciones', variables.cohorteId, variables.periodo] })
      queryClient.invalidateQueries({ queryKey: ['liquidaciones-historial'] })
    },
  })
}

export function useCerrarLiquidacion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => liquidacionesService.cerrar(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['liquidaciones'] })
    },
  })
}

export function useLiquidacionesHistorial(page: number) {
  return useQuery({
    queryKey: ['liquidaciones-historial', page],
    queryFn: () => liquidacionesService.historial(page),
  })
}

export function useExportarLiquidaciones() {
  return useMutation({
    mutationFn: ({ cohorteId, periodo }: { cohorteId: string; periodo: string }) =>
      liquidacionesService.exportar(cohorteId, periodo),
  })
}
