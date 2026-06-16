import { Card } from '@/shared/components/ui/Card'
import { Spinner } from '@/shared/components/ui/Spinner'
import { useColoquioMetrics } from '@/features/coordinacion/hooks/useColoquios'

export default function ColoquiosPage() {
  const { data: metrics, isLoading } = useColoquioMetrics()

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Panel de Coloquios</h2>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : metrics ? (
        <div className="grid grid-cols-4 gap-4">
          <Card header={<span className="text-sm font-medium text-gray-600">Alumnos Cargados</span>}>
            <p className="text-3xl font-bold text-gray-900">{metrics.total_alumnos_cargados}</p>
          </Card>
          <Card header={<span className="text-sm font-medium text-gray-600">Instancias Activas</span>}>
            <p className="text-3xl font-bold text-blue-600">{metrics.instancias_activas}</p>
          </Card>
          <Card header={<span className="text-sm font-medium text-gray-600">Reservas Activas</span>}>
            <p className="text-3xl font-bold text-yellow-600">{metrics.reservas_activas}</p>
          </Card>
          <Card header={<span className="text-sm font-medium text-gray-600">Notas Registradas</span>}>
            <p className="text-3xl font-bold text-green-600">{metrics.notas_registradas}</p>
          </Card>
        </div>
      ) : (
        <p className="text-center text-gray-500">No se pudieron cargar las métricas</p>
      )}
    </div>
  )
}
