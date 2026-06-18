import { useQuery } from '@tanstack/react-query'
import { analisisService } from '@/features/academico/services/analisisService'

export function useNotasFinales(materiaId: string) {
  return useQuery({
    queryKey: ['notas-finales', materiaId],
    queryFn: () => analisisService.getNotasFinales(materiaId),
    enabled: !!materiaId,
  })
}
