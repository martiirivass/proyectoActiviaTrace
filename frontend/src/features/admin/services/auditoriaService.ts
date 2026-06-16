import { get } from '@/shared/api/api'
import type { AuditDashboard, AuditLogFiltros, AuditLogResponse, AuditoriaFiltros } from '@/features/admin/types'

export const auditoriaService = {
  getDashboard: (filtros?: AuditoriaFiltros): Promise<AuditDashboard> =>
    get<AuditDashboard>('/audit/dashboard', { params: filtros }),

  getLog: (filtros?: AuditLogFiltros): Promise<AuditLogResponse> =>
    get<AuditLogResponse>('/audit/log', { params: filtros }),
}
