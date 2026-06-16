import { useQuery } from '@tanstack/react-query'
import { analisisService } from '@/features/academico/services/analisisService'

export function useReportes(materiaId: string) {
  return useQuery({
    queryKey: ['reportes', materiaId],
    queryFn: () => analisisService.getReportes(materiaId),
    enabled: !!materiaId,
  })
}
