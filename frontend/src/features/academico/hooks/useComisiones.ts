import { useQuery } from '@tanstack/react-query'
import { get } from '@/shared/api/api'
import type { Comision } from '@/features/academico/types'

export function useComisiones() {
  return useQuery<Comision[]>({
    queryKey: ['comisiones'],
    queryFn: () => get<Comision[]>('/materias/mis-comisiones'),
  })
}
