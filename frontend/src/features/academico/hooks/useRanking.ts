import { useQuery } from '@tanstack/react-query'
import { analisisService } from '@/features/academico/services/analisisService'

export function useRanking(materiaId: string) {
  return useQuery({
    queryKey: ['ranking', materiaId],
    queryFn: () => analisisService.getRanking(materiaId),
    enabled: !!materiaId,
  })
}
