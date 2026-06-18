import { useQuery } from '@tanstack/react-query'
import { analisisService } from '@/features/academico/services/analisisService'

export function useAtrasados(materiaId: string, busqueda?: string) {
  return useQuery({
    queryKey: ['atrasados', materiaId, busqueda],
    queryFn: () => analisisService.getAtrasados(materiaId, busqueda),
    enabled: !!materiaId,
  })
}
