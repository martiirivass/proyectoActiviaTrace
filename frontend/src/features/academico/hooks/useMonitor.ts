import { useQuery } from '@tanstack/react-query'
import { monitorService } from '@/features/academico/services/monitorService'
import type { MonitorFiltros } from '@/features/academico/types'

export function useMonitor(filtros: MonitorFiltros) {
  return useQuery({
    queryKey: ['monitor-seguimiento', filtros],
    queryFn: () => monitorService.getSeguimiento(filtros),
  })
}
