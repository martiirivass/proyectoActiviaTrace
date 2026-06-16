import { useQuery } from '@tanstack/react-query'
import { get } from '@/shared/api/api'
import type { MonitorAlumnoEntry, MonitorFiltrosCoordinacion } from '@/features/coordinacion/types'

export function useMonitorGeneral(filtros: MonitorFiltrosCoordinacion) {
  return useQuery({
    queryKey: ['monitor', 'general', filtros],
    queryFn: () => get<MonitorAlumnoEntry[]>('/monitor/general', { params: filtros }),
    keepPreviousData: true,
  })
}

export function useMonitorCoordinacion(filtros: MonitorFiltrosCoordinacion) {
  return useQuery({
    queryKey: ['monitor', 'coordinacion', filtros],
    queryFn: () => get<MonitorAlumnoEntry[]>('/monitor/coordinacion', { params: filtros }),
    keepPreviousData: true,
  })
}
