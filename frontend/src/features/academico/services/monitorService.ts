import { get } from '@/shared/api/api'
import type { MonitorEntry, MonitorFiltros } from '@/features/academico/types'

export const monitorService = {
  getSeguimiento: (filtros: MonitorFiltros): Promise<MonitorEntry[]> =>
    get<MonitorEntry[]>('/analisis/monitor-seguimiento', { params: filtros }),
}
