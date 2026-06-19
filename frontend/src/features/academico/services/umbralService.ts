import { get, patch, post } from '@/shared/api/api'
import type { UmbralMateria, UpdateUmbralRequest } from '@/features/academico/types'

export const umbralService = {
  getUmbral: (materiaId: string): Promise<UmbralMateria | null> =>
    get<UmbralMateria | null>('/calificaciones/umbral', { params: { materia_id: materiaId } }),

  updateUmbral: (data: UpdateUmbralRequest): Promise<UmbralMateria> =>
    patch<UmbralMateria>('/calificaciones/umbral', data),

  recalcular: (materiaId: string): Promise<void> =>
    post<void>('/calificaciones/umbral/recalcular', undefined, { params: { materia_id: materiaId } }),
}
