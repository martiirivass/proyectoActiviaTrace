import { post } from '@/shared/api/api'
import type { CalificacionPreview, ConfirmImportRequest, ImportResult } from '@/features/academico/types'

export const calificacionesService = {
  uploadPreview: (file: File, materiaId: string, cohorteId: string): Promise<CalificacionPreview> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('materia_id', materiaId)
    formData.append('cohorte_id', cohorteId)
    return post<CalificacionPreview>('/calificaciones/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  confirmImport: (data: ConfirmImportRequest): Promise<ImportResult> =>
    post<ImportResult>('/calificaciones/importar', data),
}
