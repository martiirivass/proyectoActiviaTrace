import { useQuery } from '@tanstack/react-query'
import { encuentrosService } from '@/features/coordinacion/services/encuentrosService'
import type { EncuentrosAdminFiltros } from '@/features/coordinacion/types'

export function useEncuentrosAdmin(filtros?: EncuentrosAdminFiltros) {
  return useQuery({
    queryKey: ['encuentros', 'admin', filtros],
    queryFn: () => encuentrosService.listAdmin(filtros),
  })
}
