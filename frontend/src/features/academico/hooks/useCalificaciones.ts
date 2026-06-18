import { useMutation, useQueryClient } from '@tanstack/react-query'
import { calificacionesService } from '@/features/academico/services/calificacionesService'
import type { ConfirmImportRequest } from '@/features/academico/types'

export function useUploadPreview() {
  return useMutation({
    mutationFn: ({
      file,
      materiaId,
      cohorteId,
    }: {
      file: File
      materiaId: string
      cohorteId: string
    }) => calificacionesService.uploadPreview(file, materiaId, cohorteId),
  })
}

export function useConfirmImport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ConfirmImportRequest) =>
      calificacionesService.confirmImport(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calificaciones'] })
      queryClient.invalidateQueries({ queryKey: ['atrasados'] })
      queryClient.invalidateQueries({ queryKey: ['ranking'] })
      queryClient.invalidateQueries({ queryKey: ['notas-finales'] })
      queryClient.invalidateQueries({ queryKey: ['reportes'] })
    },
  })
}
