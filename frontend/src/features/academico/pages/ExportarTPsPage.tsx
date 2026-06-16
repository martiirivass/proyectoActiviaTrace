import { useParams } from 'react-router-dom'
import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'
import { useExportarTPs } from '@/features/academico/hooks/useExportarTPs'

export default function ExportarTPsPage() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const exportMutation = useExportarTPs()

  const handleExport = () => {
    if (!materiaId) return
    exportMutation.mutate(materiaId)
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">
        Exportar TPs sin corregir
      </h2>
      <p className="text-sm text-gray-600">
        Descargá un archivo CSV con el listado de trabajos prácticos pendientes
        de corrección.
      </p>
      <Button
        onClick={handleExport}
        loading={exportMutation.isPending}
        disabled={exportMutation.isPending}
      >
        Exportar TPs sin corregir
      </Button>
      {exportMutation.isError && (
        <Alert
          variant="error"
          message={
            exportMutation.error?.message ??
            'Error al exportar. Intente nuevamente.'
          }
        />
      )}
    </div>
  )
}
