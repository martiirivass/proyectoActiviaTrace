import { useParams } from 'react-router-dom'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { MetricasConsolidadas } from './MetricasConsolidadas'
import { DistribucionActividades } from './DistribucionActividades'
import { useReportes } from '@/features/academico/hooks/useReportes'

export function ReportesView() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const { data: reporte, isLoading, isError, refetch } = useReportes(materiaId ?? '')

  if (isLoading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (isError) {
    return (
      <Alert variant="error" message="Error al cargar los reportes.">
        <button
          type="button"
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium underline"
        >
          Reintentar
        </button>
      </Alert>
    )
  }

  if (!reporte) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <p className="text-gray-500">
          No hay datos disponibles para esta comisión.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <MetricasConsolidadas reporte={reporte} />
      <div>
        <h3 className="mb-3 text-base font-semibold text-gray-900">
          Distribución por actividad
        </h3>
        <DistribucionActividades distribucion={reporte.distribucion_actividades} />
      </div>
    </div>
  )
}
