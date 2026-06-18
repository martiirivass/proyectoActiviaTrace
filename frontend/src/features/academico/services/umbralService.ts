import { get, patch, post } from '@/shared/api/api'
import type { UmbralMateria, UpdateUmbralRequest } from '@/features/academico/types'

export const umbralService = {
  getUmbral: (materiaId: string): Promise<UmbralMateria | null> =>
    get<UmbralMateria | null>('/umbral', { params: { materia_id: materiaId } }),

  updateUmbral: (data: UpdateUmbralRequest): Promise<UmbralMateria> =>
    patch<UmbralMateria>('/umbral', data),

  recalcular: (materiaId: string): Promise<void> =>
    post<void>('/umbral/recalcular', { materia_id: materiaId }),
}
