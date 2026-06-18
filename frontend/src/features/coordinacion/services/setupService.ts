import { post, get } from '@/shared/api/api'
import type { SelectOption } from '@/features/coordinacion/types'

export interface CreateCohorteRequest {
  identifier: string
  name: string
  vigencia_desde: string
  vigencia_hasta: string
}

export interface CreateCohorteResponse {
  id: string
  identifier: string
  name: string
}

export interface UploadProgramaRequest {
  materia_id: string
  cohorte_id: string
  file: File
}

export interface FechaEvaluacionRequest {
  materia_id: string
  fecha: string
  descripcion: string
}

export const setupService = {
  createCohorte: (data: CreateCohorteRequest): Promise<CreateCohorteResponse> =>
    post<CreateCohorteResponse>('/cohortes', data),

  getMateriasOptions: (): Promise<SelectOption[]> =>
    get<SelectOption[]>('/materias/options'),

  getCohortesOptions: (): Promise<SelectOption[]> =>
    get<SelectOption[]>('/cohortes/options'),

  uploadPrograma: (data: UploadProgramaRequest): Promise<void> => {
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('materia_id', data.materia_id)
    formData.append('cohorte_id', data.cohorte_id)
    return post<void>('/programas/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  cargarFechas: (data: FechaEvaluacionRequest[]): Promise<void> =>
    post<void>('/fechas-evaluaciones', { fechas: data }),
}
