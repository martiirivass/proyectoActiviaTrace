import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { equiposService } from '@/features/coordinacion/services/equiposService'
import type { MisEquiposFiltros, AsignacionesFiltros, AsignacionMasivaRequest, ClonarEquipoRequest, VigenciaEquipoRequest } from '@/features/coordinacion/types'

export function useMisEquipos(filtros?: MisEquiposFiltros) {
  return useQuery({
    queryKey: ['equipos', 'mis-equipos', filtros],
    queryFn: () => equiposService.getMisEquipos(filtros),
  })
}

export function useAsignaciones(filtros?: AsignacionesFiltros) {
  return useQuery({
    queryKey: ['equipos', 'asignaciones', filtros],
    queryFn: () => equiposService.getAsignaciones(filtros),
  })
}

export function useAsignacionMasiva() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: AsignacionMasivaRequest) => equiposService.asignacionMasiva(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipos'] })
    },
  })
}

export function useClonarEquipo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: ClonarEquipoRequest) => equiposService.clonarEquipo(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipos'] })
    },
  })
}

export function useModificarVigencia() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: VigenciaEquipoRequest) => equiposService.modificarVigencia(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipos'] })
    },
  })
}

export function useExportarEquipo() {
  return useMutation({
    mutationFn: ({ materiaId, carreraId, cohorteId }: { materiaId: string; carreraId: string; cohorteId: string }) =>
      equiposService.exportar(materiaId, carreraId, cohorteId),
  })
}
