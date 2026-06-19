import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { get } from '@/shared/api/api'
import type { MonitorAlumnoEntry, MonitorFiltrosCoordinacion } from '@/features/coordinacion/types'

export function useMonitorGeneral(filtros: MonitorFiltrosCoordinacion) {
  return useQuery({
    queryKey: ['monitor', 'general', filtros],
    queryFn: () => get<MonitorAlumnoEntry[]>('/analisis/monitor-general', { params: filtros }),
    placeholderData: keepPreviousData,
  })
}

export function useMonitorCoordinacion(filtros: MonitorFiltrosCoordinacion) {
  return useQuery({
    queryKey: ['monitor', 'coordinacion', filtros],
    queryFn: () => get<MonitorAlumnoEntry[]>('/analisis/monitor-seguimiento-extendido', { params: filtros }),
    placeholderData: keepPreviousData,
  })
}
