import { get } from '@/shared/api/api'
import type { EncuentroEntry, EncuentrosAdminFiltros } from '@/features/coordinacion/types'

export const encuentrosService = {
  listAdmin: (filtros?: EncuentrosAdminFiltros): Promise<EncuentroEntry[]> =>
    get<EncuentroEntry[]>('/encuentros', { params: filtros }),
}
