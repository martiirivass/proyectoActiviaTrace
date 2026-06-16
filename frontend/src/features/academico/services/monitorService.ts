import { get } from '@/shared/api/api'
import type { MonitorEntry, MonitorFiltros } from '@/features/academico/types'

export const monitorService = {
  getSeguimiento: (filtros: MonitorFiltros): Promise<MonitorEntry[]> =>
    get<MonitorEntry[]>('/monitor/seguimiento', { params: filtros }),
}
