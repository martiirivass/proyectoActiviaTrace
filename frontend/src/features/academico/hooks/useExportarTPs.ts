import { useMutation } from '@tanstack/react-query'
import { analisisService } from '@/features/academico/services/analisisService'

export function useExportarTPs() {
  return useMutation({
    mutationFn: async (materiaId: string) => {
      const blob = await analisisService.exportarTPs(materiaId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tps-sin-corregir-${materiaId}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
  })
}
