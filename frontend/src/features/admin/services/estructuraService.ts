import { get, post, put, del } from '@/shared/api/api'
import type { Carrera, CarreraFormData, Cohorte, CohorteFormData, Materia, MateriaFormData, Dictado, DictadoFormData } from '@/features/admin/types'

export const estructuraService = {
  getCarreras: (): Promise<Carrera[]> =>
    get<Carrera[]>('/admin/carreras'),

  createCarrera: (data: CarreraFormData): Promise<Carrera> =>
    post<Carrera>('/admin/carreras', data),

  updateCarrera: (id: string, data: Partial<CarreraFormData>): Promise<Carrera> =>
    put<Carrera>(`/admin/carreras/${id}`, data),

  deleteCarrera: (id: string): Promise<void> =>
    del<void>(`/admin/carreras/${id}`),

  getCohortes: (carreraId?: string): Promise<Cohorte[]> =>
    get<Cohorte[]>('/admin/cohortes', {
      params: carreraId ? { carrera_id: carreraId } : undefined,
    }),

  createCohorte: (data: CohorteFormData): Promise<Cohorte> =>
    post<Cohorte>('/admin/cohortes', data),

  updateCohorte: (id: string, data: Partial<CohorteFormData>): Promise<Cohorte> =>
    put<Cohorte>(`/admin/cohortes/${id}`, data),

  deleteCohorte: (id: string): Promise<void> =>
    del<void>(`/admin/cohortes/${id}`),

  getMaterias: (): Promise<Materia[]> =>
    get<Materia[]>('/admin/materias'),

  createMateria: (data: MateriaFormData): Promise<Materia> =>
    post<Materia>('/admin/materias', data),

  updateMateria: (id: string, data: Partial<MateriaFormData>): Promise<Materia> =>
    put<Materia>(`/admin/materias/${id}`, data),

  deleteMateria: (id: string): Promise<void> =>
    del<void>(`/admin/materias/${id}`),

  getDictados: (materiaId?: string, cohorteId?: string): Promise<Dictado[]> =>
    get<Dictado[]>('/admin/dictados', {
      params: {
        ...(materiaId && { materia_id: materiaId }),
        ...(cohorteId && { cohorte_id: cohorteId }),
      },
    }),

  createDictado: (data: DictadoFormData): Promise<Dictado> =>
    post<Dictado>('/admin/dictados', data),

  updateDictado: (id: string, data: Partial<DictadoFormData>): Promise<Dictado> =>
    put<Dictado>(`/admin/dictados/${id}`, data),

  deleteDictado: (id: string): Promise<void> =>
    del<void>(`/admin/dictados/${id}`),
}
