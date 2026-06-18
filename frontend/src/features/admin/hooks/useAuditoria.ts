import { useQuery } from '@tanstack/react-query'
import { auditoriaService } from '@/features/admin/services/auditoriaService'
import type { AuditoriaFiltros, AuditLogFiltros } from '@/features/admin/types'

export function useAuditDashboard(filtros?: AuditoriaFiltros) {
  return useQuery({
    queryKey: ['audit-dashboard', filtros],
    queryFn: () => auditoriaService.getDashboard(filtros),
    refetchInterval: 60_000,
  })
}

export function useAuditLog(filtros?: AuditLogFiltros) {
  return useQuery({
    queryKey: ['audit-log', filtros],
    queryFn: () => auditoriaService.getLog(filtros),
  })
}
